import React, { useEffect, useState } from "react";
import { Alert, Pressable, SafeAreaView, StyleSheet, Text, View } from "react-native";
import { GoogleSignin, statusCodes } from "@react-native-google-signin/google-signin";

import Button from "../../components/ui/Button";
import { ROUTES } from "../../constants/routes";
import useAuth from "../../hooks/useAuth";
import authApi from "../../services/authApi";
import { colors, fontSize, spacing } from "../../theme";

const LoginScreen = ({ navigation }) => {
  const { login } = useAuth();
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  useEffect(() => {
    GoogleSignin.configure({
      webClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID || undefined,
    });
  }, []);

  const handleGoogleSignIn = async () => {
    if (isGoogleLoading) {
      return;
    }

    setIsGoogleLoading(true);
    try {
      await GoogleSignin.hasPlayServices();
      const signInResult = await GoogleSignin.signIn();
      const idToken = signInResult?.data?.idToken || signInResult?.idToken;

      if (!idToken) {
        throw new Error("Google did not return an ID token.");
      }

      const { data } = await authApi.googleLogin(idToken);
      const userData = data.user || {
        email: data.email,
        full_name: data.full_name,
        role: data.role,
        has_profile: data.has_profile,
        application_status: data.application_status,
      };

      await login(data.token, userData);
    } catch (error) {
      if (error?.code === statusCodes.SIGN_IN_CANCELLED) {
        return;
      }
      if (error?.code === statusCodes.IN_PROGRESS) {
        return;
      }
      if (error?.code === statusCodes.PLAY_SERVICES_NOT_AVAILABLE) {
        Alert.alert("Google Sign-In", "Google Play Services are not available.");
        return;
      }
      Alert.alert("Login Failed", "Unable to sign in with Google. Please try again.");
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <View style={styles.logoCircle}>
          <Text style={styles.logoText}>AP</Text>
        </View>
        <Text style={styles.title}>Admission Portal</Text>
        <Text style={styles.subtitle}>Sign in to continue your application</Text>

        <View style={styles.actions}>
          <Button
            title="Sign in with Google"
            onPress={handleGoogleSignIn}
            loading={isGoogleLoading}
          />
          <Pressable onPress={() => navigation.navigate(ROUTES.AUTH.REGISTER)}>
            <Text style={styles.registerText}>Register with Email</Text>
          </Pressable>
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  logoCircle: {
    width: 84,
    height: 84,
    borderRadius: 42,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.md,
  },
  logoText: {
    color: colors.surface,
    fontSize: fontSize.xl,
    fontWeight: "700",
    letterSpacing: 1,
  },
  title: {
    fontSize: fontSize.xxl,
    color: colors.text,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: fontSize.md,
    color: colors.textSecondary,
    marginBottom: spacing.xl,
  },
  actions: {
    width: "100%",
    maxWidth: 360,
  },
  registerText: {
    textAlign: "center",
    color: colors.primary,
    fontSize: fontSize.md,
    fontWeight: "600",
    marginTop: spacing.md,
  },
});

export default LoginScreen;
