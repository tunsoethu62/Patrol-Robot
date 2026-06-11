// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from custom_interfaces:msg/ObstacleStatus.idl
// generated code does not contain a copyright notice

#ifndef CUSTOM_INTERFACES__MSG__DETAIL__OBSTACLE_STATUS__BUILDER_HPP_
#define CUSTOM_INTERFACES__MSG__DETAIL__OBSTACLE_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "custom_interfaces/msg/detail/obstacle_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace custom_interfaces
{

namespace msg
{

namespace builder
{

class Init_ObstacleStatus_distance
{
public:
  explicit Init_ObstacleStatus_distance(::custom_interfaces::msg::ObstacleStatus & msg)
  : msg_(msg)
  {}
  ::custom_interfaces::msg::ObstacleStatus distance(::custom_interfaces::msg::ObstacleStatus::_distance_type arg)
  {
    msg_.distance = std::move(arg);
    return std::move(msg_);
  }

private:
  ::custom_interfaces::msg::ObstacleStatus msg_;
};

class Init_ObstacleStatus_status
{
public:
  Init_ObstacleStatus_status()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ObstacleStatus_distance status(::custom_interfaces::msg::ObstacleStatus::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_ObstacleStatus_distance(msg_);
  }

private:
  ::custom_interfaces::msg::ObstacleStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::custom_interfaces::msg::ObstacleStatus>()
{
  return custom_interfaces::msg::builder::Init_ObstacleStatus_status();
}

}  // namespace custom_interfaces

#endif  // CUSTOM_INTERFACES__MSG__DETAIL__OBSTACLE_STATUS__BUILDER_HPP_
