import React from 'react';
import { View, Text } from 'react-native';

const Placeholder = ({ name }) => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
    <Text>{name} Screen</Text>
  </View>
);

export const AgentDashboardScreen = () => <Placeholder name="Agent Dashboard" />;
export const AgentRegisterScreen = () => <Placeholder name="Agent Register" />;
export const AgentCommissionsScreen = () => <Placeholder name="Agent Commissions" />;
export const AgentProfileScreen = () => <Placeholder name="Agent Profile" />;
