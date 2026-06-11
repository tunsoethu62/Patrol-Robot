import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


class VirtualSensorTF(Node):

    def __init__(self):
        super().__init__('virtual_sensor_tf')

        self.broadcaster = StaticTransformBroadcaster(self)

        t = TransformStamped()

        t.header.frame_id = "base_link"
        t.child_frame_id = "virtual_sensor_link"

        t.transform.translation.x = 0.2
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.1

        t.transform.rotation.w = 1.0

        self.broadcaster.sendTransform(t)


def main():
    rclpy.init()
    node = VirtualSensorTF()
    rclpy.spin(node)