import React from "react";
import { Text } from "react-native";

import Header from "../../components/layout/Header";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Card from "../../components/ui/Card";

const DocumentsPlaceholderScreen = () => (
  <ScreenWrapper>
    <Header title="Documents" subtitle="Upload flow starts in Week 8" />
    <Card>
      <Text>Document upload screens will be enabled in Week 8.</Text>
    </Card>
  </ScreenWrapper>
);

export default DocumentsPlaceholderScreen;
