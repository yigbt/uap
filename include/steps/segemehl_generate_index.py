import sys
import os
from abstract_step import AbstractStep

class SegemehlGenerateIndex(AbstractStep):
    '''
    segemehl is a software to map short sequencer reads to reference genomes. 
    '''

    def __init__(self, pipeline):
        super(SegemehlGenerateIndex, self).__init__(pipeline)

        self.set_cores(4)
        
        self.add_connection('in/reference_sequence')
        self.add_connection('out/segemehl_index')
        self.add_connection('out/log')

        self.require_tool('dd')
        self.require_tool('mkfifo')
        self.require_tool('pigz')
        self.require_tool('segemehl')

        self.add_option('index-basename', str, default = "")

    def runs(self, run_ids_connections_files):


        for run_id in run_ids_connections_files.keys():
            index_basename = run_id
            if self.get_option('index-basename'):
                index_basename = "%s-%s" % (
                    self.get_option('index-basename'), run_id)

            with self.declare_run(run_id) as run:
                # Get list of files for first/second read
                refseq = run_ids_connections_files[run_id]\
                         ['in/reference_sequence']

                if refseq == [None]:
                    raise StandardError("No reference sequence received.")

                # Get names of FIFOs
                refseq_fifos = list()
                index_fifo = run.add_temporary_file(
                    'segemehl-index-fifo', designation = 'output')

                with run.new_exec_group() as exec_group:
                    # 1. Create FIFOs ...
                    # 1.1 ... for the input sequence
                    for seq_file in refseq:
                        seq_fifo = run.add_temporary_file(
                            '%s-fifo' % os.path.basename(seq_file),
                            designation = 'input')
                        refseq_fifos.append(seq_fifo)

                        mkfifo_seq = [
                            self.get_tool('mkfifo'),
                            seq_fifo
                        ]
                        exec_group.add_command(mkfifo_seq)
                        # Feed reference sequence to seq_fifo
                        dd_refseq = [
                            self.get_tool('dd'),
                            'bs=4M',
                            'if=%s' % seq_file,
                            'of=%s' % seq_fifo
                        ]
                        exec_group.add_command(dd_refseq)

                    # 1.2 ... for the index to be generated
                    mkfifo_index = [
                        self.get_tool('mkfifo'),
                        index_fifo
                    ]
                    exec_group.add_command(mkfifo_index)

                    # 1. Start segemehl
                    segemehl = [
                        self.get_tool('segemehl'),
                        '--generate', index_fifo,
                        '--database', " ".join(refseq_fifos)
                    ]

                    exec_group.add_command(
                        segemehl,
                        stderr_path = run.add_output_file(
                            'log',
                            '%s-segemehl-generate-index-log.txt' % run_id,
                            refseq
                        )
                    )

                    # Read index from index_fifo
                    dd_index = [self.get_tool('dd'),
                                'bs=4M',
                                'if=%s' % index_fifo]
                    exec_group.add_command(
                        dd_index,
                        stdout_path = run.add_output_file(
                            'segemehl_index',
                            '%s.idx' % index_basename,
                            refseq)
                    )
