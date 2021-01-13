from uaperrors import StepError
import sys
import os
from logging import getLogger
from abstract_step import AbstractStep
import importlib
import subprocess

logger = getLogger('uap_logger')


class HtSeqCount(AbstractStep):
    '''
    The htseq-count script counts the number of reads overlapping a feature.
    Input needs to be a file with aligned sequencing reads and a list of genomic
    features. For more information see:

    http://www-huber.embl.de/users/anders/HTSeq/doc/count.html
    '''

    def __init__(self, pipeline):
        super(HtSeqCount, self).__init__(pipeline)

        self.set_cores(2)

        #        self.add_connection('in/alignments')
        # the BAM files
        self.add_connection('in/alignments')

        # the feature file provided by another step (e.g. cuffmerge)
        self.add_connection('in/features', optional=True, format='gtf',
                            description='reference assembly'
                            )

        # the counts per alignment
        self.add_connection('out/counts')

        self.require_tool('dd')
        self.require_tool('pigz')
        self.require_tool('htseq-count')
        self.require_tool('samtools')

        # Path to external feature file if necessary
        self.add_option('feature-file', str, optional=True)

        # [Options for 'htseq-count':]
        self.add_option('order', str, choices=['name', 'pos'],
                        optional=False)
        self.add_option('stranded', str, choices=['yes', 'no', 'reverse'],
                        optional=False)
        self.add_option('a', int, optional=True)
        self.add_option('type', str, default='exon', optional=True)
        self.add_option('idattr', str, default='gene_id', optional=True)
        self.add_option('mode', str, choices=['union', 'intersection-strict',
                                              'intersection-nonempty'],
                        default='union', optional=True)

        # [Options for 'dd':]
        self.add_option('dd-blocksize', str, optional=True, default="2M")
        self.add_option('pigz-blocksize', str, optional=True, default="2048")
        self.add_option('threads', int, default=2, optional=True,
                        description="start <n> threads (default:2)")

    def runs(self, cc):
        # Compile the list of options
        options = ['order', 'stranded', 'a', 'type', 'idattr', 'mode']

        set_options = [option for option in options if
                       self.is_option_set_in_config(option)]

        option_list = list()
        for option in set_options:
            if isinstance(self.get_option(option), bool):
                if self.get_option(option):
                    option_list.append('--%s' % option)
            else:
                option_list.append(
                    '--%s=%s' % (option, str(self.get_option(option))))

        if 'threads' in set_options:
            self.set_cores(self.get_option('threads'))

        # look for reference assembly in in-connections
        option_ref_assembly = self.get_option('feature-file')
        if option_ref_assembly is not None:
            option_ref_assembly = os.path.abspath(option_ref_assembly)
            if not os.path.isfile(option_ref_assembly):
                raise StepError(self, '%s is no file.' %
                                self.get_option('feature-file'))
        ref_assembly = cc.look_for_unique('in/features', option_ref_assembly)
        ref_per_run = cc.all_runs_have_connection('in/features')

        allignment_runs = cc.get_runs_with_connections('in/alignments')
        for run_id in allignment_runs:

            input_paths = cc[run_id]['in/alignments']
            if ref_per_run:
                # all runs come with their own reference assembly
                ref_assembly = cc['in/features'][0]
            if option_ref_assembly is None:
                # include the file in the dependencies
                input_paths.append(ref_assembly)

            # Is the alignment gzipped?
            root, ext = os.path.splitext(input_paths[0])
            is_gzipped = True if ext in ['.gz', '.gzip'] else False
            # Is the alignment in SAM or BAM format?
            if is_gzipped:
                root, ext = os.path.splitext(root)

            is_bam = False
            is_sam = False
            if ext in ['.bam']:
                is_bam = True
            elif ext in ['.sam']:
                is_sam = True
            else:
                raise StepError(
                    self, "Input file not in [SB]am format: %s" %
                    input_paths[0])

            if not (bool(is_bam) ^ bool(is_sam)):
                raise StepError(
                    self,
                    "Alignment file '%s' is neither SAM nor BAM "
                    "format" %
                    input_paths[0])

            alignments_path = input_paths[0]


            ## print some information about PATHs and python modules

            test = importlib.util.find_spec("HTSeq")
            found = test is not None
            logger.warning("\nPackage HTSeq is present: %s\n", found)

            pathvar = os.environ['PATH']
            logger.warning("PATH variable:\n %s", pathvar)

            pathvar = os.environ['PYTHONPATH']
            logger.warning("PYTHONPATH variable:\n %s", pathvar)

            which = subprocess.check_output(["which", "htseq-count"])
            logger.warning( "Which htseq-count shall be used: %s", which)

            which = subprocess.check_output(["which", "python"])
            logger.warning( "Which python shall be used: %s", which)

            logger.warning( "Path to search for modules: \n %s", sys.path)
            
            with self.declare_run(run_id) as run:
                with run.new_exec_group() as exec_group:
                    with exec_group.add_pipeline() as pipe:
                        # 1. Read alignment file in 4MB chunks
                        dd_in = [self.get_tool('dd'),
                                 'ibs=%s' % self.get_option('dd-blocksize'),
                                 'if=%s' % input_paths[0]]
                        pipe.add_command(dd_in)

                        if is_gzipped:
                            # 2. Uncompress file to STDOUT
                            pigz = [self.get_tool('pigz'),
                                    '--decompress',
                                    '--blocksize',
                                    self.get_option('pigz-blocksize'),
                                    '--processes',
                                    str(self.get_cores()),
                                    '--stdout']
                            pipe.add_command(pigz)

                        # 3. Use samtools to generate SAM output
                        if is_bam:
                            samtools = [self.get_tool('samtools'), 'view',
                                        '-']
                            pipe.add_command(samtools)

                        # 4. Count reads with htseq-count
                        htseq_count = [
                            self.get_tool('htseq-count')
                        ]
                        htseq_count.extend(option_list)

                        htseq_count.extend(['--format=sam'])

                        htseq_count.extend(['-', ref_assembly])
                        # sys.stderr.write("hts-cmd: %s\n" % htseq_count)

                        pipe.add_command(
                            htseq_count,
                            stdout_path=run.add_output_file(
                                'counts',
                                '%s-htseq_counts.txt' % run_id,
                                input_paths
                            )
                        )
