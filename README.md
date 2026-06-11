# Patrol Robot — ROS 2 Package

A four-node ROS 2 system that drives a robot in a simple forward-patrol loop, detecting obstacles with a LIDAR scanner, publishing localisation data, and broadcasting a static sensor TF frame.

---

## Architecture

```
/scan (LaserScan)
      │
      ▼
 ScannerNode  ──►  /obstacle_status (ObstacleStatus)
                          │
                          ▼
                 PatrolControllerNode  ──►  /cmd_vel (Twist)

 PoseMonitorNode  ──►  /patrol_pose (PoseStamped)
   (subscribes to /odom  OR  /amcl_pose)

 VirtualSensorTF  ──►  TF: base_link → virtual_sensor_link (static)
```

| Node | File | Purpose |
|---|---|---|
| `ScannerNode` | `scanner_node.py` | Reads `/scan`, publishes obstacle status |
| `PatrolControllerNode` | `patrol_controller_node.py` | State-machine drive loop |
| `PoseMonitorNode` | `pose_monitor_node.py` | Unified pose publisher + optional CSV log |
| `VirtualSensorTF` | `virtual_sensor_tf.py` | Static TF for the virtual sensor link |

---

## Nodes

### ScannerNode (`sensor_node`)

Subscribes to `/scan` (sensor_msgs/LaserScan), inspects the front sector, and publishes an `ObstacleStatus` message.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `threshold` | float | `0.5` | Distance (m) below which an obstacle is reported |
| `window` | int | `20` | Half-width of the front scan sector in rays |

**Topics**

| Direction | Topic | Type |
|---|---|---|
| Subscribe | `/scan` | `sensor_msgs/LaserScan` |
| Publish | `/obstacle_status` | `custom_interfaces/ObstacleStatus` |

---

### PatrolControllerNode (`patrol_controller_node`)

Implements a three-state machine: **MOVING_FORWARD → STOPPING → TURNING**, driven at 10 Hz.

```
MOVING_FORWARD ──(obstacle close)──► STOPPING
STOPPING       ──(stop_duration)───► TURNING
TURNING        ──(turn_duration + path clear)──► MOVING_FORWARD
               ──(path still blocked)──────────► (keep turning)
```

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `linear_speed` | float | `0.3` | Forward speed (m/s) |
| `angular_speed` | float | `0.5` | Turn speed (rad/s) |
| `stop_duration` | float | `1.0` | Pause before turning (s) |
| `turn_duration` | float | `3.14` | Seconds to turn (~180 ° at 1 rad/s) |

**Topics**

| Direction | Topic | Type |
|---|---|---|
| Subscribe | `/obstacle_status` | `custom_interfaces/ObstacleStatus` |
| Publish | `/cmd_vel` | `geometry_msgs/Twist` |

---

### PoseMonitorNode (`pose_monitor_node`)

Normalises either `/odom` or `/amcl_pose` into a single `/patrol_pose` topic. Optionally writes throttled pose data to a CSV file.

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `source` | string | `odom` | Input source: `odom` or `amcl` |
| `log_to_file` | bool | `false` | Enable CSV logging |
| `log_path` | string | `/tmp/patrol_pose_log.csv` | Output CSV path |
| `log_interval` | float | `1.0` | Minimum seconds between CSV rows |

**Topics**

| Direction | Topic | Type |
|---|---|---|
| Subscribe | `/odom` | `nav_msgs/Odometry` *(when source=odom)* |
| Subscribe | `/amcl_pose` | `geometry_msgs/PoseWithCovarianceStamped` *(when source=amcl)* |
| Publish | `/patrol_pose` | `geometry_msgs/PoseStamped` |

**CSV columns:** `wall_time`, `ros_time_sec`, `frame_id`, `x`, `y`, `z`, `qx`, `qy`, `qz`, `qw`

---

### VirtualSensorTF (`virtual_sensor_tf`)

Broadcasts a single static transform so the virtual sensor link is visible in TF.

| Field | Value |
|---|---|
| Parent frame | `base_link` |
| Child frame | `virtual_sensor_link` |
| Translation | x=0.2 m, y=0.0 m, z=0.1 m |
| Rotation | Identity (w=1) |

---

## Custom Interfaces

The package depends on `custom_interfaces`, which must define:

```
# custom_interfaces/msg/ObstacleStatus.msg
string status      # 'OK' or 'OBSTACLE_CLOSE'
float32 distance   # metres to nearest obstacle in front sector
```

---

## Dependencies

- ROS 2 (Humble or later recommended)
- `rclpy`
- `sensor_msgs`, `geometry_msgs`, `nav_msgs`
- `tf2_ros`
- `custom_interfaces` (see above)

---

## Building

```bash
cd ~/ros2_ws
colcon build --packages-select patrol_robot custom_interfaces
source install/setup.bash
```

---

## Running

Launch all four nodes individually (or wrap them in a launch file):

```bash
# Terminal 1 — static TF
ros2 run patrol_robot virtual_sensor_tf

# Terminal 2 — scanner
ros2 run patrol_robot scanner_node \
  --ros-args -p threshold:=0.6 -p window:=25

# Terminal 3 — pose monitor (AMCL source, with CSV logging)
ros2 run patrol_robot pose_monitor_node \
  --ros-args -p source:=amcl -p log_to_file:=true

# Terminal 4 — patrol controller
ros2 run patrol_robot patrol_controller_node \
  --ros-args -p linear_speed:=0.3 -p angular_speed:=0.5
```

---

## Tuning Tips

- **Obstacle detection sensitivity** — decrease `threshold` for later braking; increase `window` to watch a wider arc.
- **Turn angle** — `turn_duration × angular_speed ≈ angle (rad)`. For a 90° turn at 0.5 rad/s: `turn_duration = 3.14`.
- **Fail-safe behaviour** — if the front sector returns no valid LIDAR readings, `ScannerNode` defaults to `OK` (clear). Change the fallback to `OBSTACLE_CLOSE` inside `scan_callback` if you prefer a fail-safe-stop policy.
- **AMCL QoS** — `/amcl_pose` uses `TRANSIENT_LOCAL` durability; `PoseMonitorNode` matches this automatically when `source=amcl`.

---
