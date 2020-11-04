Here we summarize the tasks that should be done on our way to
establish a uap singularity container at EVE.

__ - This document will be updated regularly - __

## Get to know singularity 

* Please have a look at the singularity website: https://sylabs.io/docs/#singularity
	
## universal analysis pipeline (uap)
   
* paper: https://doi.org/10.1186/s12859-019-3219-1
* git repo: https://github.com/yigbt/uap
   
## uap singularity container

* Current singularity container on EVE: /global/apps/uap/uap_branch_fraunhofer_uge_support.sif
* Within this container we clone uap from this repository: https://github.com/yigbt/uap
* Branch https://github.com/yigbt/uap/tree/fraunhofer_uge_support

* Within this branch there is a subdirectory "singularity_container"
  with the current definition file uap-sc.def
* There is also a build_container.md file describing how the uap
  singularity container is actually build
* Since we do not have sudo rights on EVE, we need to build the
  container remotely on sylabs.io -> __account needed__!
* Please have a look at the build_container.md file to see how uap can
  be run inside the singularity container
  

### Test current uap container

* Use the current uap singularity container for testing purposes
* Therefore, you should run the following two uap example workflow
  which are also included in the git repo:

	- RNAseq-data-download.yaml
	- RNAseq-workflow-short.yaml
	
* It might happen that not all necessary tools are already installed
  in the singularity container
* Update the container definition file accordingly __but use a
  separate branch for doing so__
* Please also have a look in the other example workflows to find
  additional tools that are missing in the container (you do not have
  to run those workflows)
  
### Conda environment YAML file

* Once all necessary tools are included in the uap container, create a
  conda yaml file that saves the evironment definition in a
  reproducible way
* Update the container definition to use the conda environment yaml
  file in order to install the needed tools
* Thereby we are prohibiting that the enviroment has to be resolved
  each time the container is built and guarentees that we use exactly
  the same tools and versions with every build
  
  
### Update the container definition

* Similar to the singularity container used for deepFPlearn
  (https://github.com/yigbt/deepFPlearn) we want to split the
  container setup in a building and final stage
* This ensures smaller container in the end


## Create testing workflows

* Create a test workflow that automatically runs when new releases of
  uap are released or the uap container is re-build
* Similar to the deepFPlearn workflow:
  https://github.com/yigbt/deepFPlearn/blob/master/.github/workflows/build-singularity-container.yml
  

## Documentation

* Constantely update the wiki entries regarding singularity at the UFZ
