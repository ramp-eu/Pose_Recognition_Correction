# Backend of Pose Recognition and Correction #

This folder creates the backend of the module PRaC.
As the application is shipped with docker, you should only need to
1. build the container
1. attach your camera
1. run the application

The code is based on [OpenVino](https://github.com/openvinotoolkit/openvino), the according [Open Model Zoo](https://github.com/openvinotoolkit/open_model_zoo) and [librealsense](https://github.com/IntelRealSense/librealsense).

# how to run #
Start the application using `docker-compose up` since all necessary parameters and mounts are present in the compose file.
The app can provide visual output to the user.
In order for this to work the local X11 is shared with the container.
Please find further information with your search engine of choice.
A good source is to look at the ROS-wiki [docker with GUI](https://wiki.ros.org/docker/Tutorials/GUI) and [docker-compose with GUI](https://wiki.ros.org/docker/Tutorials/Compose#Using_GUI.27s_with_compose).

## docker-compose ##
Provided is a docker-compose file or easy setup.
Be aware that you may need to adapt the provided user to your real setup.
By providing `user: 1000:44` we are becoming the user with `uid=1000:gid=44`.
`uid=1000` is the first real user on debian-based systems and vary for your setup - find out with `echo $UID`.
`gid=44` belongs to the video group on ubuntu 20.04 and can differ for your system - find out with `cat /etc/group | grep video` and look for number in there.
If you do not want to have graphical output, please run the application in headless mode by changing the RUN command in docker-compose.yaml to
```
command: python3 wpc.py --headless True
```

## docker ##
If you do not want to use docker-compose you are free to run the container stand-alone.
Make sure to share your X11 or run the demo in headless mode by calling
```
python3 wpc.py --headless True
```
