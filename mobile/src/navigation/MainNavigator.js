import React from "react";
import useAuth from "../hooks/useAuth";
import { StudentTabs } from "./StudentTabs";
import { AgentTabs } from "./AgentTabs";

const MainNavigator = () => {
  const { user } = useAuth();

  if (user?.role === "agent") {
    return <AgentTabs />;
  }

  return <StudentTabs />;
};

export default MainNavigator;
