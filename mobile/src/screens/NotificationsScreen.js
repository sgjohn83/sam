import React from "react";
import { Text } from "react-native";

import Header from "../components/layout/Header";
import ScreenWrapper from "../components/layout/ScreenWrapper";
import Card from "../components/ui/Card";

const NotificationsScreen = () => (
  <ScreenWrapper>
    <Header title="Notifications" subtitle="Updates from admission office" />
    <Card>
      <Text>No new notifications.</Text>
    </Card>
  </ScreenWrapper>
);

export default NotificationsScreen;
