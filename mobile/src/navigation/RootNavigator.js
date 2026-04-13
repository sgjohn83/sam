import React from "react";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import useAuth from "../hooks/useAuth";
import Spinner from "../components/ui/Spinner";
import CreateProfileScreen from "../screens/profile/CreateProfileScreen";
import { ROUTES } from "../constants/routes";
import AuthNavigator from "./AuthNavigator";
import MainNavigator from "./MainNavigator";

const Stack = createNativeStackNavigator();

const RootNavigator = () => {
  const { isLoading, isAuthenticated, hasProfile } = useAuth();

  if (isLoading) {
    return <Spinner fullScreen size="large" />;
  }

  if (!isAuthenticated) {
    return <AuthNavigator />;
  }

  if (!hasProfile) {
    return (
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          gestureEnabled: false,
        }}
      >
        <Stack.Screen name={ROUTES.PROFILE.CREATE} component={CreateProfileScreen} />
      </Stack.Navigator>
    );
  }

  return <MainNavigator />;
};

export default RootNavigator;
