import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Home, Users, UserPlus, IndianRupee, User } from 'lucide-react-native';
import { AgentDashboardScreen } from '../screens/agent/AgentDashboardScreen';
import { AgentStudentsStack } from './AgentStudentsStack';
import { AgentRegisterScreen } from '../screens/agent/AgentRegisterScreen';
import { AgentCommissionsScreen } from '../screens/agent/AgentCommissionsScreen';
import { AgentProfileScreen } from '../screens/agent/AgentProfileScreen';

const Tab = createBottomTabNavigator();

export function AgentTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#2563EB',
        tabBarInactiveTintColor: '#6B7280',
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="Dashboard"
        component={AgentDashboardScreen}
        options={{ tabBarIcon: ({ color, size }) => <Home color={color} size={size} /> }}
      />
      <Tab.Screen
        name="Students"
        component={AgentStudentsStack}
        options={{ tabBarIcon: ({ color, size }) => <Users color={color} size={size} /> }}
      />
      <Tab.Screen
        name="Register"
        component={AgentRegisterScreen}
        options={{
          tabBarIcon: ({ color, size }) => <UserPlus color={color} size={size} />,
          tabBarLabel: 'Add Student',
        }}
      />
      <Tab.Screen
        name="Commissions"
        component={AgentCommissionsScreen}
        options={{ tabBarIcon: ({ color, size }) => <IndianRupee color={color} size={size} /> }}
      />
      <Tab.Screen
        name="Profile"
        component={AgentProfileScreen}
        options={{ tabBarIcon: ({ color, size }) => <User color={color} size={size} /> }}
      />
    </Tab.Navigator>
  );
}
