import csv
import os
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry

# amcl_pose is also a PoseWithCovarianceStamped
from geometry_msgs.msg import PoseWithCovarianceStamped


class PoseMonitorNode(Node):
    def __init__(self):
        super().__init__('pose_monitor_node')

        # ------------------------------------------------------------------
        # Parameters
        # ------------------------------------------------------------------
        self.declare_parameter('source', 'odom')          # 'odom' or 'amcl'
        self.declare_parameter('log_to_file', False)       # write CSV log
        self.declare_parameter('log_path', '/tmp/patrol_pose_log.csv')
        self.declare_parameter('log_interval', 1.0)        # seconds between file writes

        self.source      = self.get_parameter('source').value
        self.log_to_file = self.get_parameter('log_to_file').value
        self.log_path    = self.get_parameter('log_path').value
        self.log_interval = self.get_parameter('log_interval').value

        # ------------------------------------------------------------------
        # Publisher
        # ------------------------------------------------------------------
        self.pose_pub = self.create_publisher(PoseStamped, '/patrol_pose', 10)

        # ------------------------------------------------------------------
        # Subscriber — chosen by 'source' parameter
        # ------------------------------------------------------------------
        # /amcl_pose uses a latched-style QoS (transient local) so we match it
        amcl_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        if self.source == 'amcl':
            self.subscription = self.create_subscription(
                PoseWithCovarianceStamped,
                '/amcl_pose',
                self.amcl_callback,
                amcl_qos,
            )
            self.get_logger().info('PoseMonitorNode subscribing to /amcl_pose')
        else:
            self.subscription = self.create_subscription(
                Odometry,
                '/odom',
                self.odom_callback,
                10,
            )
            self.get_logger().info('PoseMonitorNode subscribing to /odom')

        # ------------------------------------------------------------------
        # Optional CSV logger
        # ------------------------------------------------------------------
        self._csv_file   = None
        self._csv_writer = None
        self._last_log_time = self.get_clock().now()

        if self.log_to_file:
            self._open_csv()

        self.get_logger().info(
            f'PoseMonitorNode ready — source={self.source}, '
            f'log_to_file={self.log_to_file}'
        )

    # ----------------------------------------------------------------------
    # Subscribers callbacks
    # ----------------------------------------------------------------------

    def odom_callback(self, msg: Odometry):
        """Convert nav_msgs/Odometry → geometry_msgs/PoseStamped and publish."""
        pose_stamped = PoseStamped()
        pose_stamped.header = msg.header          # keeps frame_id ('odom') and stamp
        pose_stamped.pose   = msg.pose.pose        # strip the covariance wrapper

        self._publish_and_log(pose_stamped)

    def amcl_callback(self, msg: PoseWithCovarianceStamped):
        """Convert geometry_msgs/PoseWithCovarianceStamped → PoseStamped and publish."""
        pose_stamped = PoseStamped()
        pose_stamped.header = msg.header           # frame_id is typically 'map'
        pose_stamped.pose   = msg.pose.pose        # strip the covariance wrapper

        self._publish_and_log(pose_stamped)

    # ----------------------------------------------------------------------
    # Core logic
    # ----------------------------------------------------------------------

    def _publish_and_log(self, pose_stamped: PoseStamped):
        """Publish on /patrol_pose, log to terminal, optionally write to CSV."""
        self.pose_pub.publish(pose_stamped)

        p = pose_stamped.pose.position
        o = pose_stamped.pose.orientation

        # Terminal log
        self.get_logger().info(
            f'[POSE] x={p.x:.3f}  y={p.y:.3f}  z={p.z:.3f} | '
            f'qx={o.x:.3f}  qy={o.y:.3f}  qz={o.z:.3f}  qw={o.w:.3f} | '
            f'frame={pose_stamped.header.frame_id}'
        )

        # Throttled CSV write
        if self.log_to_file and self._csv_writer is not None:
            now = self.get_clock().now()
            elapsed = (now - self._last_log_time).nanoseconds / 1e9
            if elapsed >= self.log_interval:
                stamp = pose_stamped.header.stamp
                ros_time = stamp.sec + stamp.nanosec * 1e-9
                self._csv_writer.writerow([
                    datetime.utcnow().isoformat(),
                    f'{ros_time:.4f}',
                    pose_stamped.header.frame_id,
                    f'{p.x:.4f}', f'{p.y:.4f}', f'{p.z:.4f}',
                    f'{o.x:.4f}', f'{o.y:.4f}', f'{o.z:.4f}', f'{o.w:.4f}',
                ])
                self._csv_file.flush()
                self._last_log_time = now

    # ----------------------------------------------------------------------
    # CSV helpers
    # ----------------------------------------------------------------------

    def _open_csv(self):
        os.makedirs(os.path.dirname(self.log_path) or '.', exist_ok=True)
        self._csv_file   = open(self.log_path, 'w', newline='')
        self._csv_writer = csv.writer(self._csv_file)
        self._csv_writer.writerow([
            'wall_time', 'ros_time_sec', 'frame_id',
            'x', 'y', 'z',
            'qx', 'qy', 'qz', 'qw',
        ])
        self.get_logger().info(f'Pose log opened: {self.log_path}')

    def _close_csv(self):
        if self._csv_file is not None:
            self._csv_file.close()
            self.get_logger().info(f'Pose log closed: {self.log_path}')

    # ----------------------------------------------------------------------
    # Shutdown
    # ----------------------------------------------------------------------

    def destroy_node(self):
        self._close_csv()
        super().destroy_node()


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main(args=None):
    rclpy.init(args=args)
    node = PoseMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()