import gym
import numpy as np
import os
import rospy
import roslaunch
import subprocess
import time
import math

from gym import utils, spaces
from gym_gazebo.envs import gazebo_env
from gym.utils import seeding
from std_srvs.srv import Empty

import actionlib
from simple_movement.msg import FlyToAction , FlyToGoal
from geometry_msgs.msg import PoseStamped, Pose
# from octomap_msgs.msg import Octomap
# import octomap
# from libraries import conversions
from sensor_msgs.msg import PointCloud2
import sensor_msgs.point_cloud2 as pc2
# import pcl_ros.point_cloud as pcl
import sys

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

import collections

def print_dbg(data):
    # print(data)
    pass

def print_dbg2(data):
    print(data)
    # pass
    

AGENT_HISTORY_LENGTH = 4
RESIZED_X = 200
RESIZED_Y = 200
RESIZED_Z = 200
RESIZED_DATA = 2 #is voxel full is voxel empty
MAX_NUM_POINTS = 125000
T_FACTOR = 5

class GazeboSlamExplorationEnv(gazebo_env.GazeboEnv):
    CUBE_SIZE = 1
    MAX_TIME_EPISODE = 60*3

    def _pause(self, msg):
        programPause = raw_input(str(msg))

    def position_callback(self, data):
        self.position = data.pose

    def map_callback(self, data):
        # print("Map callback called")
        tmp_point_cloud = []
        tmp_point_cloud.append((self.position.position.x,self.position.position.y,self.position.position.z,1))       
        i=0
        for p in pc2.read_points(data, skip_nans=True):
            # print("x : ",p[0] ," y: " , p[1] ," z: ",p[2])
            tmp_point_cloud.append((p[0],p[1],p[2],0))
            i+=1
        self.len_point_cloud = len(tmp_point_cloud)
        # print("PC shape: ",np.shape(tmp_point_cloud)," i:", i)
        self.point_cloud = tmp_point_cloud
        
        # print_dbg2(('The length of the point cloud is: ', (self.len_point_cloud)))

    def __init__(self,config=None):
        # Launch the simulation with the given launchfile name
        gazebo_env.GazeboEnv.__init__(self, "GazeboSlamExploration-v0.launch")

        self.espisode_num = 0
        self.action_space = spaces.Discrete(26)
        # self.observation_space = spaces.Box(low=0, high=1, shape=(RESIZED_X, RESIZED_Y, RESIZED_Z, RESIZED_DATA), dtype=np.uint8)
        self.observation_space = spaces.Box(low=-np.Inf, high=np.Inf, shape=(MAX_NUM_POINTS, 4), dtype=np.float)
        self.reward_range = (-np.inf, np.inf)

        self.max_distance = 0
        self.episode_time = 0
        self.prev_map_size = 0
        self.point_cloud = []
        self.len_point_cloud = 0
        self.num_actions = 0
        self.reset_proxy = rospy.ServiceProxy('/gazebo/reset_world', Empty)
        self.trajectory_len = 0
        # Defining client for Fly to position
        self.client = actionlib.SimpleActionClient('fly_to', FlyToAction)
        self.client.wait_for_server()

        self.position = Pose()
        # Subscribing to the position of the drone
        rospy.Subscriber("/position_drone", PoseStamped, self.position_callback)

        # Subscribing to the map
        rospy.Subscriber("/map_points", PointCloud2 , self.map_callback)

        self.reset_octomap = rospy.ServiceProxy("/octomap_server/reset", Empty)
        self.reset_point_cloud_map = rospy.ServiceProxy("/map_pcl/reset", Empty)
        # countdown = 5
        # while countdown > 0:
        #     print("Taking off in %ds" % countdown)
        #     countdown -= 1
        #     time.sleep(1)
        self._seed()
        

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _state(self, action):
        return discretized_ranges, done

    def step(self, action ): #num_thread
        
        # The robot can move in a 3d environment so the robot is placed in a cube 3x3 that indicates the directions where it can go
        # Define 27 action one for each sub box of the big box
        # F = Forward
        # B = Backwards
        # U = Up
        # D = Down
        # L = Left
        # R = Right
        # Combinations of thes basic direction can be used. Example: FUR -> Means the upper, right corner going forward of the 3x3 box
        # Starting from the Up and going in anticlock versus
        # the 27th is the action to stay still
        # Front Line

        goal = FlyToGoal()

        goal.pose = PoseStamped()
        goal.pose.header.frame_id='map'
        goal.distance_converged = 0.2
        goal.yaw_converged = 0.2
        goal.pose.pose.position.x = self.position.position.x
        goal.pose.pose.position.y = self.position.position.y
        goal.pose.pose.position.z = self.position.position.z

        position_before_step = np.array((self.position.position.x,self.position.position.y,self.position.position.z))

        goal.pose.pose.orientation.x = 0 
        goal.pose.pose.orientation.y = 0
        goal.pose.pose.orientation.z = 0
        goal.pose.pose.orientation.w = 1
        self.num_actions +=1
        if action == 0:  # FORWARD 
            print_dbg((self.num_actions," Going Forward"))
            goal.pose.pose.position.x = self.position.position.x+1
        elif action == 1:  # FU
            print_dbg((self.num_actions," Going FU"))
            goal.pose.pose.position.x = self.position.position.x+1
            goal.pose.pose.position.z = self.position.position.z+1
        elif action == 2:  # FUL
            print_dbg((self.num_actions," Going FUL"))
            goal.pose.pose.position.x = self.position.position.x+1
            goal.pose.pose.position.z = self.position.position.z+1
            goal.pose.pose.position.y = self.position.position.y-1
        elif action == 3:  # FL
            print_dbg((self.num_actions," Going FL"))
            goal.pose.pose.position.x = self.position.position.x+1
            goal.pose.pose.position.y = self.position.position.y-1

        elif action == 4:  # FDL
            print_dbg((self.num_actions," Going FDL"))
            goal.pose.pose.position.x = self.position.position.x+1
            goal.pose.pose.position.z = self.position.position.z-1
            goal.pose.pose.position.y = self.position.position.y-1

        elif action == 5:  # FD
            print_dbg((self.num_actions," Going FD"))
            goal.pose.pose.position.x = self.position.position.x+1
            goal.pose.pose.position.z = self.position.position.z-1

        elif action == 6:  # FDR
            print_dbg((self.num_actions," Going FDR"))
            goal.pose.pose.position.x = self.position.position.x+1
            goal.pose.pose.position.z = self.position.position.z-1
            goal.pose.pose.position.y = self.position.position.y+1

        elif action == 7:  # FR
            print_dbg((self.num_actions," Going FR"))
            goal.pose.pose.position.x = self.position.position.x+1
            goal.pose.pose.position.y = self.position.position.y+1

        elif action == 8:  # FUR
            print_dbg((self.num_actions," Going FUR"))
            goal.pose.pose.position.x = self.position.position.x+1
            goal.pose.pose.position.z = self.position.position.z+1
            goal.pose.pose.position.y = self.position.position.y+1


        # Central line
        elif action == 9:  # U
            print_dbg((self.num_actions," Going U"))
            goal.pose.pose.position.z = self.position.position.z+1

        elif action == 10:  # UL
            print_dbg((self.num_actions," Going UL"))
            goal.pose.pose.position.z = self.position.position.z+1
            goal.pose.pose.position.y = self.position.position.y-1

        elif action == 11:  # L
            print_dbg((self.num_actions," Going L"))
            goal.pose.pose.position.y = self.position.position.y-1

        elif action == 12:  # DL
            print_dbg((self.num_actions," Going DL"))
            goal.pose.pose.position.z = self.position.position.z-1
            goal.pose.pose.position.y = self.position.position.y-1

        elif action == 13:  # D
            print_dbg((self.num_actions," Going D"))
            goal.pose.pose.position.z = self.position.position.z-1

        elif action == 14:  # DR
            print_dbg((self.num_actions," Going DR"))
            goal.pose.pose.position.z = self.position.position.z-1
            goal.pose.pose.position.y = self.position.position.y+1

        elif action == 15:  # R
            print_dbg((self.num_actions," Going R"))
            goal.pose.pose.position.y = self.position.position.y+1

        elif action == 16:  # UR
            print_dbg((self.num_actions," Going UR"))
            goal.pose.pose.position.z = self.position.position.z+1
            goal.pose.pose.position.y = self.position.position.y+1


        # Back line
        elif action == 17:  # B
            print_dbg((self.num_actions," Going B"))
            goal.pose.pose.position.x = self.position.position.x-1

        elif action == 18:  # BU
            print_dbg((self.num_actions," Going BU"))
            goal.pose.pose.position.x = self.position.position.x-1
            goal.pose.pose.position.z = self.position.position.z+1

        elif action == 19:  # BUL
            print_dbg((self.num_actions," Going BUL"))
            goal.pose.pose.position.x = self.position.position.x-1
            goal.pose.pose.position.z = self.position.position.z+1
            goal.pose.pose.position.y = self.position.position.y-1

        elif action == 20:  # BL
            print_dbg((self.num_actions," Going BL"))
            goal.pose.pose.position.x = self.position.position.x-1
            goal.pose.pose.position.y = self.position.position.y-1

        elif action == 21:  # BDL
            print_dbg((self.num_actions," Going BDL"))
            goal.pose.pose.position.x = self.position.position.x-1
            goal.pose.pose.position.z = self.position.position.z-1
            goal.pose.pose.position.y = self.position.position.y-1

        elif action == 22:  # BD
            print_dbg((self.num_actions," Going BD"))
            goal.pose.pose.position.x = self.position.position.x-1
            goal.pose.pose.position.z = self.position.position.z-1

        elif action == 23:  # BDR
            print_dbg((self.num_actions," Going BDR"))
            goal.pose.pose.position.x = self.position.position.x-1
            goal.pose.pose.position.z = self.position.position.z-1
            goal.pose.pose.position.y = self.position.position.y+1

        elif action == 24:  # BR
            print_dbg((self.num_actions," Going BR"))
            goal.pose.pose.position.x = self.position.position.x-1
            goal.pose.pose.position.y = self.position.position.y+1

        elif action == 25:  # BUR
            print_dbg((self.num_actions," Going BUR"))
            goal.pose.pose.position.x = self.position.position.x-1
            goal.pose.pose.position.z = self.position.position.z+1
            goal.pose.pose.position.y = self.position.position.y+1

        # elif action == 26:  # STILL
        #     print_dbg((self.num_actions,"Stay Still"))
        #     goal.pose.pose.position.x = self.position.position.x
        #     goal.pose.pose.position.z = self.position.position.z
        #     goal.pose.pose.position.y = self.position.position.y
        


        # Send /set_position message and wait till the point is not reached
        # print ( "num: ", num_thread, "goal:" )
        # print ( "x: ",goal.pose.pose.position.x )
        # print ( "y: ",goal.pose.pose.position.y )  
        # print ( "z: ",goal.pose.pose.position.z ) 
        self.client.send_goal(goal)

        self.client.wait_for_result()

        result = self.client.get_result()
        # print("The result is: ",result.steps, type(result))

        observation = self._get_state()

        #### to count number of one (cam be used for reward)
        unique, counts = np.unique(observation, return_counts=True)
        # print(dict(zip(unique, counts)))
        position_after_step = np.array((self.position.position.x,self.position.position.y,self.position.position.z))
        # print("Distance done: ", np.linalg.norm(position_after_step-position_before_step) )
        self.trajectory_len += np.linalg.norm(position_after_step-position_before_step)
        

        #Condition for end the episode: If episode time is higher then MAX_TIME_EPISODE
        # print ( rospy.Duration(self.MAX_TIME_EPISODE) )
        print("Elapsed time: ", (rospy.Time.now()-self.episode_time).to_sec(),"                         ", end='\r')
        if (rospy.Time.now()-self.episode_time > rospy.Duration(self.MAX_TIME_EPISODE)) or (self.len_point_cloud >= MAX_NUM_POINTS): # or self.position.position.x >= 10 
        # if (self.len_point_cloud >= MAX_NUM_POINTS): # or self.position.position.x >= 10 
            done = True
            print("Episode completed!                \nTotal number of points: {} in: {} time. Number of steps: {}".format(self.len_point_cloud,(rospy.Time.now()-self.episode_time).to_sec(),self.num_actions))
            print("Distance done total: ", self.trajectory_len)
        else:
            done = False
        
        #Reward function
        if done or (self.num_actions <= 5):
            reward = 0
        elif result.steps == 1 : #If it choose to go to a position it can't negative reward
            reward = -100
        else:                
            reward = int((self.len_point_cloud-self.prev_map_size)/100) - T_FACTOR
        self.prev_map_size=self.len_point_cloud

        # print_dbg2(("The reward is: ", reward ))
        return observation, reward, done, {}

    def _killall(self, process_name):
        pids = subprocess.check_output(["pidof", process_name]).split()
        for pid in pids:
            os.system("kill -9 "+str(pid))

    def _get_state(self):  # Get position and map
        # pos = np.array([self.position.position.x,self.position.position.y,self.position.position.z])
        # if(self.len_point_cloud != 0 ):
        #     pc_map = np.array(self.point_cloud)
        # else:
        #     pc_map = np.zeros((0,3))
        # print(pc_map.shape)
        
        #trying to voxelize the point cloud it cover a 100x100x100m box with a resolution  of 0.5m
        # bound = 100
        # res = 0.5
        # dim = int(bound/res)
        # voxel_map = np.zeros((dim,dim,dim,2))
        # #inserting the drone in the voxel map 
        # voxel_map[int((pos[0]+bound/2)/res)][int((pos[1]+bound/2)/res)][int((pos[2]+bound/2)/res)][0]=1
        # voxel_map[int((pos[0]+bound/2)/res)][int((pos[1]+bound/2)/res)][int((pos[2]+bound/2)/res)][1]=1
        # for p in pc_map:
        #     #each index is the position in the specific axes plu half the maximum bound (for having negative position)
        #     #and then divided by the resolution for the specific index
        #     voxel_map[int((p[0]+bound/2)/res)][int((p[1]+bound/2)/res)][int((p[2]+bound/2)/res)][0]=1

        #for plot the map it is just for test it crash after first time
        # fig =plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        # x,y,z,d=[],[],[],[]
        
        # for i in range(dim):
        #     for j in range(dim):
        #         for k in range(dim):
        #             if( voxel_map[i][j][k][0]==1):
        #                 x.append(i);
        #                 y.append(j)
        #                 z.append(k)
        #                 d.append(voxel_map[i][j][k][1])
        # img = ax.scatter(x,y,z,c=d, cmap=plt.hot())
        # fig.colorbar(img)
        # plt.show()

        #copy point cloud to be sure callback doesn't modify list during returning state
        tmp_point_cloud = self.point_cloud
        if(self.len_point_cloud < MAX_NUM_POINTS):
            for i in range(MAX_NUM_POINTS - len(tmp_point_cloud)):
                tmp_point_cloud.append((0,0,0,-1))
        else:
            tmp_point_cloud = tmp_point_cloud[:-(len(tmp_point_cloud)-MAX_NUM_POINTS)]
        # print("PC shape after padding: ",np.shape(tmp_point_cloud))
        points = np.asarray(tmp_point_cloud)
        # print("points type",type(points))
        # print(points)
        # print("points.shape: ", points.shape)

        return points

    def reset(self):
        print_dbg2("Resetting the environment")
        # Resets the state of the environment and returns an initial observation.
        rospy.wait_for_service('/gazebo/reset_world')
        rospy.wait_for_service("/octomap_server/reset")
        rospy.wait_for_service("/map_pcl/reset")
        self.prev_map_size = 0
        self.episode_time = 0
        print_dbg2("Ended episode: "+ str(self.espisode_num))
        self.espisode_num += 1
        self.num_actions = 0
        self.trajectory_len = 0
        # Reset octomap
        try:
            # print ("Resetting octomap")
            self.reset_octomap()
            # print ("Octomap resetted")
        except rospy.ServiceException as exc:
            print("Service reset octomap did not process request: " + str(exc))

        try:
            # print ("Resetting point cloud map")
            self.reset_point_cloud_map()
            # print ("Point Cloud Map resetted")
        except rospy.ServiceException as exc:
            print("Service reset point cloud map did not process request: " + str(exc))
        
        try:
            # print("resetting proxy")
            # reset_proxy.call()
            self.reset_proxy()
        except (rospy.ServiceException) as exc:
            print("/gazebo/reset_world service call failed" + str(exc))


        self.episode_time = rospy.Time.now()
        # print("Resetting complete")
        return self._get_state()




