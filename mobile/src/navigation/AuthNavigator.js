import React from "react";
import { createStackNavigator } from "@react-navigation/stack";

import LoginScreen from "../screens/auth/LoginScreen";
import RegisterScreen from "../screens/auth/RegisterScreen";
import VerifyOtpScreen from "../screens/auth/VerifyOtpScreen";
import { ROUTES } from "../constants/routes";

const Stack = createStackNavigator();

const AuthNavigator = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name={ROUTES.AUTH.LOGIN} component={LoginScreen} />
    <Stack.Screen name={ROUTES.AUTH.REGISTER} component={RegisterScreen} />
    <Stack.Screen name={ROUTES.AUTH.VERIFY_OTP} component={VerifyOtpScreen} />
  </Stack.Navigator>
);

export default AuthNavigator;
