import React from "react";
import { Text } from "react-native";

import Header from "../../components/layout/Header";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Card from "../../components/ui/Card";

const ApplicationPlaceholderScreen = () => (
  <ScreenWrapper>
    <Header title="Application" subtitle="Application form flow starts in Week 9" />
    <Card>
      <Text>Application form screens will be enabled in Week 9.</Text>
    </Card>
  </ScreenWrapper>
);

export default ApplicationPlaceholderScreen;
