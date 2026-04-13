import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { AgentStudentListScreen } from '../screens/agent/AgentStudentListScreen';
import { AgentStudentDetailScreen } from '../screens/agent/AgentStudentDetailScreen';

const Stack = createNativeStackNavigator();

export function AgentStudentsStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="StudentList" component={AgentStudentListScreen} />
      <Stack.Screen name="StudentDetail" component={AgentStudentDetailScreen} />
    </Stack.Navigator>
  );
}
