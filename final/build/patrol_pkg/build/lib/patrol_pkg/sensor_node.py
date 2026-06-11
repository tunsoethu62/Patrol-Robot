import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from custom_interfaces.msg import ObstacleStatus


class ScannerNode(Node):
    def __init__(self):
        super().__init__('sensor_node')

        # --- Tunable parameters (set at launch with --ros-args -p name:=value) ---
        self.declare_parameter('threshold', 0.5)   # obstacle distance in metres
        self.declare_parameter('window', 20)        # half-width of front scan sector (rays)

        self.threshold = self.get_parameter('threshold').value
        self.window = self.get_parameter('window').value

        # --- Subscriber & Publisher ---
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        self.publisher = self.create_publisher(
            ObstacleStatus,
            '/obstacle_status',
            10
        )

        self.get_logger().info(
            f'ScannerNode ready — threshold={self.threshold} m, window=±{self.window} rays'
        )

    # ------------------------------------------------------------------
    # Callback
    # ------------------------------------------------------------------

    def scan_callback(self, msg: LaserScan):
        ranges = msg.ranges

        # Determine front index based on angle
        front_angle = 0.0  # 0 radians = front
        center_index = int((front_angle - msg.angle_min) / msg.angle_increment)

        # Clamp window to avoid going out of bounds
        half = min(self.window, center_index, len(ranges) - center_index - 1)

        # Slice the front sector
        raw_slice = ranges[center_index - half : center_index + half + 1]

        # FIX 1 & 3 — strip inf and nan before calling min()
        valid_ranges = [
            r for r in raw_slice
            if math.isfinite(r) and msg.range_min <= r <= msg.range_max
        ]

        status_msg = ObstacleStatus()

        if not valid_ranges:
            # FIX 3 — no valid readings in the front sector; treat as clear
            # (or raise a warning — change to "OBSTACLE_CLOSE" if you prefer fail-safe)
            self.get_logger().warn(
                'Front sector has no valid range readings — defaulting to OK'
            )
            status_msg.distance = float(msg.range_max)
            status_msg.status = 'OK'
        else:
            min_distance = min(valid_ranges)
            status_msg.distance = float(min_distance)
            status_msg.status = (
                'OBSTACLE_CLOSE' if min_distance < self.threshold else 'OK'
            )

        self.publisher.publish(status_msg)
        self.get_logger().info(
            f'[SCAN] distance={status_msg.distance:.3f} m  status={status_msg.status}'
        )


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main(args=None):
    rclpy.init(args=args)
    node = ScannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()