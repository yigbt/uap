# Build singularity container 

- to build the container on EVE we need sudo
- therefore, we use the remote building option 

```bash
singularity build --remote /global/apps/uap/uap_v1.0.sif uap-sc.def
```

Please note the current testing version that is functional was build with this command:

```bash
singularity build --remote /global/apps/uap/uap_branch_fraunhofer_uge_support.sif uap-sc.def
```

# Test the container locally 

- we can run the container on bioinf2 without uge support

```bash
singularity run /global/apps/uap/uap_branch_fraunhofer_uge_support.sif RNAseq2countData.config.yaml status
```

# Enter container interactively

```bash
singularity exec /global/apps/uap/uap_branch_fraunhofer_uge_support.sif bash
```

After entering the container, the conda environment has to be loaded:

```bash
. /usr/local/miniconda3/etc/profile.d/conda.sh
conda activate uap_python3_v1.0
```

# Updates on the uap singularity integration process

* I created a new branch from the  yigbt uap repo
* adapted the qsub template file and updated the submit_to_cluster.py script
* manually adapt the submit_to_cluster script such that the pipeline is running
* functional branch is uge_support at https://github.com/yigbt/uap/tree/uge_support

* FUNCTIONAL CONTAINER: uap_branch_YIGBT_uge_support.sif

* PROBLEM: in submit_to_cluster I hard coded the command to run uap within a singularity container

* suggested the general changes to Christopf for uge support
* this should be included in their current master branch which was forked from yigbt: https://github.com/fraunhofer-izi/uap


