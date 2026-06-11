import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory('patrol_pkg')
    turtlebot3_desc_path = get_package_share_directory('turtlebot3_description')
    
    world = os.path.join(pkg_share, 'worlds', 'world_test.world')
    urdf_file = os.path.join(turtlebot3_desc_path, 'urdf', 'turtlebot3_burger.urdf')

    
    with open(urdf_file, 'r') as infp:
        robot_desc = infp.read().replace('${namespace}', '')

    gazebo = ExecuteProcess(
        cmd=['gazebo', '--verbose', world, '-s', 'libgazebo_ros_factory.so'],
        output='screen'
    )

    spawn_turtlebot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'turtlebot3',
            '-file', os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'models', 'turtlebot3_burger', 'model.sdf'),
            '-x', '0', '-y', '0', '-z', '0.01'
        ],
        output='screen'
    )

    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_desc,
            'use_sim_time': True
        }]
    )

    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '0.2', '0.0', '0.1', '0', '0', '0', 
            'base_link', 'virtual_sensor_link'
        ],
        parameters=[{'use_sim_time': True}]
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(pkg_share, 'rviz', 'patrol_config.rviz')],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        spawn_turtlebot,
        static_tf,
        robot_state_publisher,
        rviz
    ])