#!/usr/bin/env python

import rospy, cv2, cv_bridge, numpy
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
import math


class Follower:
    def __init__(self):
        self.bridge = cv_bridge.CvBridge()
        self.image_sub = rospy.Subscriber('/camera/rgb/image_raw', Image, self.image_callback)
        self.centroid_publisher = rospy.Publisher('centroid', Image, queue_size=1)
        self.cmd_vel_pub = rospy.Publisher('cmd_vel', Twist, queue_size=1)
        self.twist = Twist()
        self.logcount = 0
        self.lostcount = 0

    def image_callback(self, msg):

        # get image from camera
        image = self.bridge.imgmsg_to_cv2(msg)

        # filter out everything that's not yellow
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_yellow = numpy.array([ 40, 0, 0])
        upper_yellow = numpy.array([ 120, 255, 255])
        mask = cv2.inRange(hsv,  lower_yellow, upper_yellow)
        masked = cv2.bitwise_and(image, image, mask=mask)

    # clear all but a 20 pixel band near the top of the image
        h, w, d = image.shape
        search_top = int(3 * h /4)
        search_bot = search_top + 20
        mask[0:search_top, 0:w] = 0
        mask[search_bot:h, 0:w] = 0
        
        # cv2.imshow("band", mask)

    # Computing the "centroid" and display a red circle to denote it
        M = cv2.moments(mask)
        self.logcount += 1
        print("M00 %d %d" % (M['m00'], self.logcount))

        if M['m00'] > 0:
            cx = int(M['m10']/M['m00']) + 100
            cy = int(M['m01']/M['m00'])
            cv2.circle(image, (cx, cy), 20, (0,0,255), -1)

            # Move at 0.3 M/sec
            # add a turn if the centroid is not in the center
            # Hope for the best. Lots of failure modes.
            err = cx - w/2
            self.twist.linear.x = 0.3
            # Making the relevant transaformation corrections along the way, the 0.5 constant allows it to make more gradual adjustments
            self.twist.angular.z = 0.5 * math.tanh(-float(err) / 100)
            self.cmd_vel_pub.publish(self.twist)
            #So that the centroid is seen
            self.centroid_publisher.publish(self.bridge.cv2_to_imgmsg(image))
        else:
            #Code when it doubles back on the same line
            #When the robot cannot find the line, it will stop and start turning till it finds one
            self.twist.linear.x = 0
            self.twist.angular.z = 1
            self.cmd_vel_pub.publish(self.twist)

        cv2.imshow("image", image)
        cv2.waitKey(3)

rospy.init_node('follower')
follower = Follower()
rospy.spin()