# Jenkins Job Builder
## Overview
[Jenkins Job Builder](http://docs.openstack.org/infra/jenkins-job-builder/) is a command line tool for configuring [Jenkins](http://jenkins-ci.org/), using [YAML](http://www.yaml.org/) format configuration files.

Online documentation is available at http://docs.openstack.org/infra/jenkins-job-builder/

## Defaults
This section holds default values used by `jenkins-job` and `../create-config.py`. 

 - **name**: name of this defaults section. currently only one exists, but it it possible to define multiple default sections.
 - **repo_dir**: relative path from the Jenkins job workspace to the top of the source code tree
 - **subpath**: empty by default. generated by `create-config.py` as the path under `repo_dir` where a given tree lives
 - **is_disabled**: local variable name to disable building a tree; becomes the JJB variable `disabled`
 - **mozconfig**: empty by default. generated by `create-config.py` from mozconfig entries in `config.yml`
 - **hg_revision**: local variable, used by JJB's [SCM module](http://docs.openstack.org/infra/jenkins-job-builder/scm.html) (as `revision`). determines Mercurial branch or tag name to track
 - ** hg_revision_type**: local variable, used by JJB's [SCM module](http://docs.openstack.org/infra/jenkins-job-builder/scm.html) (as `revision-type`). determines revision type to use, either `branch` or `tag`.

## Job templates
### Indexing job
This is your standard repo indexing job; nearly every job will be this type. 

 - **name**: job entries in `../jobs.yml` that match this name pattern (i.e. `{name}_index)`) will use this template for generating a Jenkins job
 - **defaults**: which defaults section to use
 - **project-type**: Jenkins project type
 - **disabled**: JJB variable populated by `create-config.py` from the `is_disabled` local variable in `../config.yml`
 - **quiet-period**: job triggered by SCM polling may have a minimum time between builds, to prevent frequent commits from generating many build jobs. default value is in `../config.yml`
 - **triggers**: 
     - **pollscm**: standard jobs use SCM polling to start builds, with polling happening based on the `schedule` variable.
 - **properties**: 
     - **heavy-job**: the [Heavy Job plugin](https://wiki.jenkins-ci.org/display/JENKINS/Heavy+Job+Plugin) is used to prevent resource starvation; it's configuration is pulled in here with the `job_weight` variable
 - **publishers**: 
     - **email**: notifications of job status is enabled here with recipients defined in `mail_rcpts`
 - **wrappers**:
     - **timestamps**: enable time stamps in a job's console output
     - **inject**: using the [EnvInject plugin](https://wiki.jenkins-ci.org/display/JENKINS/EnvInject+Plugin), create a `.mozconfig` file if the tree includes a `mozconfig` section
 - **scm**: SCM type is determined programmatically by `create-config`, so this section contains variables for both mercurial and git
     - **url**: URL of the repo
     - **revision**: Mercurial; branch or tag to track, from the local variable `hg_revision`
     - **revision-type**: Mercurial; whether revision to track is branch or tag, from the local variable `hg_revision_type`
     - **subdir**: Mercurial: concatenation of `repo_dir`, from the default section, and `subpath`, which is programmatically built by `creat-config.py` based on the repo's URL (e.g. the subpath for hg.m.o/foo/bar would be foo/bar)
     - **basedir**: Git; same as above
     - **skip-tag**: Git; do not attempt to tag this build
 - **builders**: which builder(s) to run for this job, currently only `docker-run`
     - **name**: name of the tree as seen in `config.yml` and `dxr.config`
     - **docker_img**: which docker image is used to index this tree
     - **docker_vol**: local volume mounting, to connect the source tree on the docker host to the running image

### Tree job
A special job type that indexes a tree of repos, which allows for cheap cross-tree searching. This job does not do SCM polling, nor does it update any of the trees under the parent; it's a simple timed job that does a simple text index of the tree.

There are only two differences between tree jobs and standard indexing jobs:

 - **name**: job entries in `../jobs.yml` that match this name pattern (i.e. `{name}_tree)`) will use this template for generating a Jenkins job
 - **triggers**: uses a timed trigger, a la cron
     - **timed**: schedule is set as above, using the `schedule` variable

### Builder
Currently only one builder exists, using a docker image to index a tree.

 - **name**: docker-run. used by all job templates
 - **builders**: a shell-based job, which pulls the docker image and then runs `index.sh {name}` on the image
