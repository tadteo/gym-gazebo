FROM osrf/ros:melodic-desktop-full

WORKDIR /root/

RUN apt update && \
    apt upgrade -y && \
    apt-get install -y \
    apt-utils \
    python3-pip python-pip python3-vcstool python3-pyqt4 \
    pyqt5-dev-tools \
    libbluetooth-dev libspnav-dev \
    pyqt4-dev-tools libcwiid-dev \
    cmake gcc g++ qt4-qmake libqt4-dev \
    libusb-dev libftdi-dev \
    python3-defusedxml \
    ros-melodic-octomap-msgs        \
    ros-melodic-joy                 \
    ros-melodic-geodesy             \
    ros-melodic-octomap-ros         \
    ros-melodic-control-toolbox     \
    ros-melodic-pluginlib	       \
    ros-melodic-trajectory-msgs     \
    ros-melodic-control-msgs	       \
    ros-melodic-std-srvs 	       \
    ros-melodic-nodelet	       \
    ros-melodic-urdf		       \
    ros-melodic-rviz		       \
    ros-melodic-kdl-conversions     \
    ros-melodic-eigen-conversions   \
    ros-melodic-tf2-sensor-msgs     \
    ros-melodic-pcl-ros \
    ros-melodic-navigation \
    ros-melodic-sophus \
    #libdynamicedt3d-dev \ 
    gfortran \
    python-skimage \
    psmisc \
    python-tk \
    net-tools \
    htop \
    tmux \
    git
    # swig \
    # valgrind

# RUN pip install --upgrade gym h5py tensorflow-gpu keras==2.3.1 pandas liveplot pydot pyparsing scikit-image==0.14.2 ray requests ray[rllib] ray[debug]
RUN pip3 install --upgrade pip
RUN pip3 install -U cmake tensorflow-gpu tensorboard scikit-build opencv-python-headless pandas keras ray ray[debug] rospkg netifaces empy 
RUN pip3 install ray[rllib] matplotlib

# RUN pip install tensorfow-gpu ??

#For Deep Q learning
# RUN cd ~ && git clone git://github.com/Theano/Theano.git
# RUN cd ~/Theano/ && python setup.py develop

RUN git clone -b releases/0.8.0 https://github.com/ray-project/ray.git

RUN mkdir -p /root/ros_ws/src && cd /root/ros_ws/src && \
    git clone https://github.com/OctoMap/octomap_mapping.git \
    && git clone https://bitbucket.org/DataspeedInc/velodyne_simulator.git \
    && git clone https://github.com/Moes96/servo_pkg.git \
    && git clone -b movement_as_service https://github.com/tadteo/simple_movement.git \
    && git clone https://github.com/tadteo/map_pcl.git 

RUN echo "source /opt/ros/melodic/setup.bash" >> ~/.bashrc
RUN cd ~/ros_ws/ && /bin/bash -c "source /opt/ros/melodic/setup.bash && catkin_make -j8"
RUN echo "source /root/ros_ws/devel/setup.bash" >> /root/.bashrc
RUN echo "alias killgazebogym='killall -9 rosout roslaunch rosmaster gzserver nodelet robot_state_publisher gzclient'" >> /root/.bashrc
RUN echo "alias run_a3c='python3 ~/gym-gazebo/examples/slam_exploration/slam_exploration_a3c.py'" >> /root/.bashrc
RUN echo "alias run_dqn='python3 ~/gym-gazebo/examples/slam_exploration/slam_exploration_dqn.py'" >> /root/.bashrc
RUN echo "alias run_qlearn='python3 ~/gym-gazebo/examples/slam_exploration/slam_exploration_qlearn.py'" >> /root/.bashrc
RUN echo "alias run_ray='python3 ~/gym-gazebo/examples/slam_exploration/slam_exploration_ray.py'" >> /root/.bashrc
RUN echo "export ROS_PYTHON_VERSION=3" >> /root/.bashrc

# nvidia-container-runtime
# ENV NVIDIA_VISIBLE_DEVICES \
#    ${NVIDIA_VISIBLE_DEVICES:-all}
# ENV NVIDIA_DRIVER_CAPABILITIES \
#    ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics



VOLUME [ "/root/gym-gazebo" ]
VOLUME [ "/root/ray_results" ]
# VOLUME [ "/root/ros_ws"]

#When needed for the installation
# RUN cd ~ && git clone --single-branch --branch develop https://github.com/TadielloM/gym-gazebo.git
# RUN pip install -e ~/gym-gazebo
# RUN cd ~/gym-gazebo/gym_gazebo/envs/installation && bash setup_melodic.bash 
# RUN cd ~/gym-gazebo/gym_gazebo/envs/installation && bash drone_velodyne_setup.bash 

# RUN cd /root/gym-gazebo/gym_gazebo/envs/slam_exploration/libraries && swig -python -c++ conversions.i
# RUN cd /root/gym-gazebo/gym_gazebo/envs/slam_exploration/libraries && g++ -c -Wall -fpic conversions_wrap.cxx -I/usr/include/python2.7 -I/opt/ros/melodic/include/
# RUN cd /root/gym-gazebo/gym_gazebo/envs/slam_exploration/libraries && g++ -shared conversions_wrap.o -L/opt/ros/melodic/lib -loctomap -lm -o _conversions.so

COPY ./initialize_env.sh /
ENTRYPOINT ["/initialize_env.sh"]
CMD ["bash"]