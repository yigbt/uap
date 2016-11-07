import sys
import os
from logging import getLogger
from abstract_step import AbstractStep

logger = getLogger('uap_logger')

class ChromHmmBinarizeBam(AbstractStep):
    '''
    This command converts coordinates of aligned reads into binarized data form
    from which a chromatin state model can be learned. The binarization is based
    on a poisson background model. If no control data is specified the parameter
    to the poisson distribution is the global average number of reads per bin.
    If control data is specified the global average number of reads is
    multiplied by the local enrichment for control reads as determined by the
    specified parameters. Optionally intermediate signal files can also be
    outputted and these signal files can later be directly converted into binary
    form using the BinarizeSignal command.
    '''

    def __init__(self, pipeline):
        super(ChromHmmBinarizeBam, self).__init__(pipeline)

        self.set_cores(4)
        
        self.add_connection('in/alignments')
        self.add_connection('out/cellmarkfiletable')
        self.add_connection('out/chromhmm_binarization')
        
        self.require_tool('ChromHMM')
        self.require_tool('ln')
        self.require_tool('mkdir')
        self.require_tool('printf')
        self.require_tool('tar')
        self.require_tool('ls')
        self.require_tool('xargs')
        
        self.add_option('chrom_sizes_file', str, optional = False,
                        descritpion = "File containing chromosome size "
                        "information generated by 'fetchChromSizes'")
        self.add_option('cell_mark_files', dict, optional = False,
                        description = "A dictionary where the keys are the "
                        "names of the run and the values are lists of lists. "
                        "The lists of lists describe the content of a "
                        "'cellmarkfiletable' files as used by 'BinarizeBam'. "
                        "But instead of file names use the run ID for the "
                        "mark and control per line. "
                        "That is a tab delimited file where each row contains "
                        "the cell type or other identifier for a groups of "
                        "marks, then the associated mark, then the name of a "
                        "BAM file, and optionally a corresponding control BAM "
                        "file. If a mark is missing in one cell type, but not "
                        "others it will receive a 2 for all entries in the "
                        "binarization file and -1 in the signal file. If the "
                        "same cell and mark combination appears on multiple "
                        "lines, then the union of all the reads across entries "
                        "is taken except for control data where each unique "
                        "file is only counted once.")

        # ChromHMM BinarizeBam Options
        self.add_option('b', int, optional = True,
                        description = "The number of base pairs in a bin "
                        "determining the resolution of the model learning and "
                        "segmentation. By default this parameter value is set "
                        "to 200 base pairs.")
#        self.add_option('c', str, optional = True,
#                        description = "A directory containing the control "
#                        "input files. If this is not specified then the "
#                        "inputbamdir is used. If no control files are specified "
#                        "then by default a uniform background will be used in "
#                        "determining the binarization thresholds.")
        self.add_option('center', bool, optional = True,
                        description = "If this flag is present then the center "
                        "of the interval is used to determine the bin to "
                        "assign a read. This can make sense to use if the "
                        "coordinates are based on already extended reads. If "
                        "this option is selected, then the strand information "
                        "of a read and the shift parameter are ignored. By "
                        "default reads are assigned to a bin based on the "
                        "position of its 5' end as determined from the strand "
                        "of the read after shifting an amount determined by "
                        "the -n shift option.")
        self.add_option('e', int, optional = True,
                        description = "Specifies the amount that should be "
                        "subtracted from the end coordinate of a read so that "
                        "both coordinates are inclusive and 0 based. The "
                        "default value is 1 corresponding to standard bed "
                        "convention of the end interval being 0-based but not "
                        "inclusive.")
        self.add_option('f', int, optional = True,
                        description = "This indicates a threshold for the fold "
                        "enrichment over expected that must be met or exceeded "
                        "by the observed count in a bin for a present call. "
                        "The expectation is determined in the same way as the "
                        "mean parameter for the poission distribution in terms "
                        "of being based on a uniform background unless control "
                        "data is specified. This parameter can be useful when "
                        "dealing with very deeply and/or unevenly sequenced "
                        "data. By default this parameter value is 0 meaning "
                        "effectively it is not used.")
        self.add_option('g', int, optional = True,
                        description = "This indicates a threshold for the "
                        "signal that must be met or exceeded by the observed "
                        "count in a bin for a present call. This parameter can "
                        "be useful when desiring to directly place a threshold "
                        "on the signal. By default this parameter value is 0 "
                        "meaning effectively it is not used.")
        self.add_option('n', int, optional = True,
                        description = "The number of bases a read should be "
                        "shifted to determine a bin assignment. Bin assignment "
                        "is based on the 5' end of a read shifted this amount "
                        "with respect to the strand orientation. By default "
                        "this value is 100.")
 #       self.add_option('o', str, optional = True,
 #                       description = "This specifies the directory to which "
 #                       "control data should be printed. The files will be "
 #                       "named CELL_CHROM_controlsignal.txt. Control data "
 #                       "will only be outputted if there are control bed files "
 #                       "present and an output control directory is specified.")
        self.add_option('p', float, optional = True,
                        description = "This option specifies the tail "
                        "probability of the poisson distribution that the "
                        "binarization threshold should correspond to. The "
                        "default value of this parameter is 0.0001.")
#        self.add_option('peaks', bool, optional = True,
#                        description = "This option specifies to treat the bed "
#                        "files as peak calls directly and give a '1' call to "
#                        "any bin overlapping a peak call.")
        self.add_option('s', int, optional = True,
                        description = "The amount that should be subtracted "
                        "from the interval start coordinate so the interval is "
                        "inclusive and 0 based. Default is 0 corresponding to "
                        "the standard bed convention.")
        self.add_option('strictthresh', bool, optional = True,
                        description = "If this flag is present then the "
                        "poisson threshold must be strictly greater than the "
                        "tail probability, otherwise by default the largest "
                        "integer count for which the tail includes the poisson "
                        "threshold probability is used.")
        self.add_option('u', int, optional = True,
                        description = "An integer pseudocount that is "
                        "uniformly added to every bin in the control data in "
                        "order to smooth the control data from 0. The default "
                        "value is 1.")
        self.add_option('w', int, optional = True,
                        description = "This determines the extent of the "
                        "spatial smoothing in computing the local enrichment "
                        "for control reads. The local enrichment for control "
                        "signal in the x-th bin on the chromosome after "
                        "adding pseudocountcontrol is computed based on the "
                        "average control counts for all bins within x-w and "
                        "x+w. If no controldir is specified, then this option "
                        "is ignored. The default value is 5.")

    def runs(self, run_ids_connections_files):

        options = ['b', 'center', 'e', 'f', 'g', 'n', 'p',
                   's', 'strictthresh', 'u', 'w']

        set_options = [option for option in options if \
                       self.is_option_set_in_config(option)]

        option_list = list()
        for option in set_options:
            if isinstance(self.get_option(option), bool):
                # Only set option if it is True
                if self.get_option(option):
                    option_list.append('-%s' % option)
            else:
                option_list.append('-%s' % option)
                option_list.append(str(self.get_option(option)))


        # We need to create a cell-mark-file table file. Should look something
        # like this:
        #
        # cell1 mark1 cell1_mark1.bed cell1_control.bed
        # cell1 mark2 cell1_mark2.bed cell1_control.bed
        # cell2 mark1 cell2_mark1.bed cell2_control.bed
        # cell2 mark2 cell2_mark2.bed cell2_control.bed
        #
        # The control file is optional!!!

        # How can we get the cell and mark information?
        # Cell = key of self.get_option(control)
        # Mark = value of self.get_option(control)


        cell_mark_files = self.get_option('cell_mark_files')
        for run_id in cell_mark_files.keys():
            # Create a new run
            with self.declare_run(run_id) as run:
                # Store cellmarkfiletable path in 'cmft_path'
                cmft_path = ""
                # Set everything up to run ChromHMM
                with run.new_exec_group() as pre_chromhmm:
                    # Create a temporary directory ...
                    bam_dir = run.add_temporary_directory('bam-files')
                    mkdir = [self.get_tool('mkdir'), bam_dir]
                    pre_chromhmm.add_command(mkdir)

                    # List with all input BAM files
                    input_files = list()
                    # List containing lines for 'cellmarkfiletable'
                    cellmarkfiletable = list()
                    # ... and link all required BAM files into it
                    # line = a list of max. length four
                    # line[0] = name/identifier for cell type
                    # line[1] = name/identifier for histone mark (or similar)
                    # line[2] = run ID identifiying mark information
                    # line[3] = run ID identifiying control information
                    for line in cell_mark_files[run_id]:
                        # Begin of line
                        bol = ""
                        bol += "%s\t%s" % (line[0], line[1])
                        # Check length of each list (line): must be 3 or 4
                        if len(line) not in [3, 4]:
                            logger.error("List [%s] of run '%s' should have 3 "
                                         "or 4 elements, but it has %s." %
                                         (", ".join(line), run_id, len(line)))

                        # Run IDs of marks are the third entry per line
                        mark_files = run_ids_connections_files[line[2]]\
                                     ['in/alignments']
                        control_files = list()
                        try:
                            # Run IDs of controls are the fourth entry per line
                            control_files = run_ids_connections_files[line[2]]\
                                            ['in/alignments']
                        except:
                            pass

                        # Assemble the cellmarkfiletable data
                        def link_file(bam_dir, f, pre_chromhmm):
                            # Mark links as temporary
                            temp_link = run.add_temporary_file(
                                os.path.join(
                                    os.path.split(bam_dir)[1],
                                    os.path.basename(f)
                                )
                            )
                            
                            ln = [
                                self.get_tool('ln'),
                                '--symbolic', str(f),
                                str(temp_link)
                            ]
                            pre_chromhmm.add_command(ln)
                            return temp_link
                    
                        # If mark and control run IDs given:
                        if mark_files and control_files:
                            input_files.extend( mark_files + control_files )
                            mc = [(m, c) for m in mark_files \
                                  for c in control_files]
                            for i in mc:
                                cellmarkfiletable.append(
                                    "%s\t%s\t%s" %
                                    (bol,
                                     os.path.basename(
                                         link_file(bam_dir, i[0], pre_chromhmm)
                                     ),
                                     os.path.basename(
                                         link_file(bam_dir, i[1], pre_chromhmm)
                                     )
                                 )
                                )
                        # If only mark files are given
                        elif mark_files:
                            input_files.extend( mark_files )
                            for f in mark_files:
                                cellmarkfiletable.append(
                                    "%s\t%s" %
                                    (bol,
                                     os.path.basename(
                                         link_file(bam_dir, f, pre_chromhmm)
                                     )
                                 )
                                )
                        else:
                            logger.error(
                                "Couldn't find proper files for run '%s'"
                                % run_id)

                    # Write cellmarkfiletable to disk using printf
                    cmft_path = run.add_output_file(
                            'cellmarkfiletable',
                            '%s.cellmarkfiletable' % run_id,
                            input_files
                    )
                    printf = [self.get_tool('printf'),
                              "\n".join(cellmarkfiletable)]
                    pre_chromhmm.add_command(
                        printf,
                        stdout_path = cmft_path
                    )

                    # Create directory for ChromHMM *_binary.txt files
                    binary_dir = run.add_temporary_directory('binary-files')
                    mkdir = [self.get_tool('mkdir'), binary_dir]

                # Assemble the ChromHMM BinarizeBam command
                with run.new_exec_group() as binarizebam:
                    chromhmm = [ self.get_tool('ChromHMM'),
                                 'BinarizeBam']
                    chromhmm.extend(option_list)
                    chromhmm.extend([
                        self.get_option('chrom_sizes_file'),
                        bam_dir,
                        cmft_path,
                        binary_dir
                    ])
                    binarizebam.add_command(chromhmm)

                # Need to tar the created <cell>_<chrom>_binary.txt files,
                # because it is impossible to know in advance which files will
                # be created by ChromHMM
                with run.new_exec_group() as pack_binary:
                    with pack_binary.add_pipeline() as pack_binary_pipe:
                        # List content of directory with *_binary.txt files
                        ls = [self.get_tool('ls'), '-1', binary_dir]
                        # Pipe ls output
                        pack_binary_pipe.add_command(ls)
                        # Call xargs to call tar (circumventing glob pattern)
                        xargs = [self.get_tool('xargs'),
                                 '--delimiter', '\n',
                                 self.get_tool('tar'),
                                 '--create',
                                 '--directory',
                                 binary_dir,
                                 '--gzip',
                                 '--remove-files',
                                 '--verbose',
                                 '--file',
                                 run.add_output_file(
                                     'chromhmm_binarization',
                                     '%s_binary_files.tar.gz' % run_id,
                                     input_files)
                             ]
                        pack_binary_pipe.add_command(xargs)
