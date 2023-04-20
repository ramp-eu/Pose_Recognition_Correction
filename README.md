# Pose Detection and Tracking #

## Background ##
The cognitive HRI package supports Human Machine Collaboration (HMC) aiming at combining human flexibility with repeatability of automated factory entities, such as cobots, for improving working conditions while pursuing better performances.
So, what does this means, in simple words?
There will be an analysis of how a human, a worker, works by using one or more pieces of equipment at the shopfloor.
The goal of this analysis is to provide an improved way of working.
Let’s see the following example: SUPSI and GESTALT provide software packages that monitor specific human attributes in order to detect both worker perceived exertion level (detected by the fatigue monitoring system,FAMS) and posture (detected by the Ergonomic package, PRaC).
This information is the input for a further decision-making package, the intervention manager, in order to re-organize the working cell for improving worker conditions and getting better performances.
So, long story short, based on the example in hand, cognitive HRI improves the working process by improving the worker’s physical conditions and vice versa.

### Objective ###
What is the submodule for?

By applying image processing algorithms to visual data we are able to compute certain postures key figures, like the angles between arms and upper body, indicating the physical stress level of the observed working situation.
Our solution focusses explicitly on a GDPR-compliant implementation, since assessing individuals and working situations with cameras can be felt an invasion of privacy.
The resulting, anonymized working posture assessment can then be used to organize the work place in a way that individual adjustments ensure less physical stress and increase the workers health.


## Install ##
Installation must meet certain criteria to be runnable.

### software requirements ###
The module is developed using docker and docker-compose.
All necessary software is included into the containers and no additional software is needed.
If you want to en/disable a debugging UI you can set `BACKEND_VISUALIZATION=1/0`.
Depending on this value you will need to share your X11 and enable `DISPLAY` environment.

### hardware requirements ###
Installation relies on having a camera plugged into the computer running the software - therefore all devices are mounted into the container.
We tested with Azure Kinect, Intel RealSense and built-in webcams.

## Usage ##
You can start the software with supplied docker-compose file.
As usual with docker-based deployments you will have to fetch the images from the registry.
When visiting `localhost:3000` in your browser, you will see an interface which reads its values from the Orion Broker, so when you see changing values everything works as expected.

## Testing ##
You can test the module with a local webcam.
Please be aware that computing a three-dimensional score from two-dimensional images involves estimating depth and therefore is of limited accuracy.
Therefore, we suggest the usage of rgbd-cameras and computing the score on the measured three-dimensional data.

## Feedback ##
This module is intended to be used as is and is maintained internally.
Please do not file issues or bug reports as this repo is only mirrored from private repos.

## Licence ##
This module and all file in here are licensed under *MIT License* as can be seen in [LICENSE.md](./LICENSE.md).
