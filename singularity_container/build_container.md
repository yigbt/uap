# Introduction

Normally, uap can be run on EVE locally on a compute node, or the jobs
that are created by uap can be submitted to the EVE cluster via the
univa grid engine (uge).

A common uap call would look like this:
```bash
uap project_description.yaml status
uap project_description.yaml submit-to-cluster
```

With the encapsulation of uap within a singularity container, we want
to increase the reproducibility and decrease our dependencies on the
local EVE cluster architecture.

However, a main problem is the fact that we are __not__ able to
communicate with uge from inside the singularity container and we
hence need a workaround to submit jobs to the grid engine. Right now
this problem ist solved by using ssh commands to propagate commands
from inside the container. 

A remaining issue is the call of the singulairy container to run
single jobs. In the current branch of uap which is used in the
singularity container, we hard-coded the command to run singularity
with the specific container version. This has to be updated in the
future.

The container definition file is uap-sc.def

# Build singularity container 

Since we need to build the container on EVE we need sudo rights (and
we don't have them), we need to use the remote building option:

```bash
singularity build --remote /global/apps/uap/uap_v1.0.sif uap-sc.def
```

Please note, the current testing version that is functional was build with this command:

```bash
singularity build --remote /global/apps/uap/uap_branch_fraunhofer_uge_support.sif uap-sc.def
```

Make sure that you are in the correct branch of the repo when running the build command!

# Enter container interactively

```bash
singularity exec /global/apps/uap/uap_branch_fraunhofer_uge_support.sif bash
```

After entering the container, the conda environment has to be loaded:

```bash
Singularity> . /usr/local/miniconda3/etc/profile.d/conda.sh
Singularity> conda activate uap_python3_v1.0
```

With this setup, all tools that have been installed within the conda
environment should be callable, i.e.:
```bash
Singularity> fastqc --version
```


# Run uap with the singularity container

Before actually running uap, we need to specify the workflow with a
specific yaml file, like those example-workflows in the git
repo. These yaml files describe the complete analysis workflow,
including output directories, temp directories, files to use, analysis
steps, etc...

To have a quick look on the analysis and which steps will be run, we
can use the _status_ command from uap:
```bash
singularity run /global/apps/uap/uap_branch_fraunhofer_uge_support.sif workflow_description.yaml status
```

To start the analysis we need to call:
```bash
singularity run /global/apps/uap/uap_branch_fraunhofer_uge_support.sif workflow_description.yaml submit-to-cluster
```


# Updates on the uap singularity integration process

* I created a new branch from the yigbt uap repo

* adapted the qsub template file and updated the submit_to_cluster.py
  script

* manually adapt the submit_to_cluster script such that the pipeline
  is running

* functional branch is fraunhofer_uge_support at
  https://github.com/yigbt/uap/tree/fraunhofer_uge_support

* FUNCTIONAL CONTAINER:
  /global/apps/uap/uap_branch_fraunhofer_uge_support.sif

* PROBLEM: in submit_to_cluster I hard coded the command to run uap
  within a singularity container

* suggested the general changes to Christopf for uge support

* this should be included in their current master branch which was
  forked from yigbt: https://github.com/fraunhofer-izi/uap

* Within the PRE_JOB_COMMAND in the submit-to-cluster script, we want
  to define an alias for uap such that the actual call of uap starts
  the whole container (which needs to be executable) instead of the
  local version of uap
  
* The actual PRE_JOB_COMMAND is definde in the workflow yaml file
  which should make it quite easy to define the workaround without
  interfering with the uap code itself.
 
* Create a separate option for cluster specifications in the
  cluster-specific-commands.yaml file such that specific singularity
  settings, like \$TASK_ID, are kept separate from 'normal' uge
  settings where we only need $TASK_ID without the backslash.
  Maybe call this _singularity\_uge_

* What about the lmod specifications that are written to all submit
  scripts?  Are those still necessary then?
