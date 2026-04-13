import React from "react";
import { Text } from "react-native";

import Header from "../../components/layout/Header";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";

const SeatDetailsScreen = () => (
  <ScreenWrapper>
    <Header title="Seat Details" subtitle="Allocated branch and quota" />
    <Card>
      <Text style={{ marginBottom: 12 }}>Branch: CSE</Text>
      <Text style={{ marginBottom: 12 }}>Quota: OBC</Text>
      <Badge text="Fee Pending" color="yellow" />
    </Card>
  </ScreenWrapper>
);

export default SeatDetailsScreen;
