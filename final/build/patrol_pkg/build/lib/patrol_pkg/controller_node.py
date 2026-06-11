import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from custom_interfaces.msg import ObstacleStatus
from enum import Enum


class PatrolState(Enum):
    MOVING_FORWARD = 'moving_forward'
    STOPPING = 'stopping'
    TURNING = 'turning'


class PatrolControllerNode(Node):
    def __init__(self):
        super().__init__('patrol_controller_node')

        # --- Parameters ---
        self.declare_parameter('linear_speed', 0.3)       # m/s forward speed
        self.declare_parameter('angular_speed', 0.5)      # rad/s turn speed
        self.declare_parameter('stop_duration', 1.0)      # seconds to pause before turning
        self.declare_parameter('turn_duration', 3.14)     # seconds to turn (~180° at 1 rad/s)

        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.stop_duration = self.get_parameter('stop_duration').value
        self.turn_duration = self.get_parameter('turn_duration').value

        # --- Publisher & Subscriber ---
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.obstacle_sub = self.create_subscription(
            ObstacleStatus,
            '/obstacle_status',
            self.obstacle_callback,
            10
        )

        # --- State machine ---
        self.state = PatrolState.MOVING_FORWARD
        self.state_start_time = self.get_clock().now()

        # --- Control loop timer (10 Hz) ---
        self.control_timer = self.create_timer(0.1, self.control_loop)

        # Latest obstacle reading
        self.latest_status = 'OK'
        self.latest_distance = float('inf')

        self.get_logger().info('Patrol Controller started — state: MOVING_FORWARD')

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def obstacle_callback(self, msg: ObstacleStatus):
        """Cache the latest obstacle status from SensorNode."""
        self.latest_status = msg.status
        self.latest_distance = msg.distance

    def control_loop(self):
        """State machine executed at 10 Hz."""
        now = self.get_clock().now()
        elapsed = (now - self.state_start_time).nanoseconds / 1e9  # seconds

        if self.state == PatrolState.MOVING_FORWARD:
            self._handle_moving_forward()

        elif self.state == PatrolState.STOPPING:
            self._handle_stopping(elapsed)

        elif self.state == PatrolState.TURNING:
            self._handle_turning(elapsed)

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def _handle_moving_forward(self):
        if self.latest_status == 'OBSTACLE_CLOSE':
            self.get_logger().info(
                f'Obstacle at {self.latest_distance:.2f} m — switching to STOPPING'
            )
            self._publish_velocity(0.0, 0.0)
            self._transition_to(PatrolState.STOPPING)
        else:
            self._publish_velocity(self.linear_speed, 0.0)

    def _handle_stopping(self, elapsed: float):
        self._publish_velocity(0.0, 0.0)
        if elapsed >= self.stop_duration:
            self.get_logger().info('Stop complete — switching to TURNING')
            self._transition_to(PatrolState.TURNING)

    def _handle_turning(self, elapsed: float):
        self._publish_velocity(0.0, self.angular_speed)
        if elapsed >= self.turn_duration:
            if self.latest_status == 'OK':
                self.get_logger().info('Turn complete — switching to MOVING_FORWARD')
                self._transition_to(PatrolState.MOVING_FORWARD)
            else:
                # Keep turning until the path looks clear
                self.get_logger().info(
                    'Obstacle still close after turn — continuing to turn'
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _publish_velocity(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.cmd_vel_pub.publish(msg)

    def _transition_to(self, new_state: PatrolState):
        self.state = new_state
        self.state_start_time = self.get_clock().now()

    def destroy_node(self):
        """Send a stop command on shutdown."""
        self.get_logger().info('Shutting down — stopping robot')
        self._publish_velocity(0.0, 0.0)
        super().destroy_node()


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main(args=None):
    rclpy.init(args=args)
    node = PatrolControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()