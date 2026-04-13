import React, { useState } from "react";
import { StyleSheet, Text } from "react-native";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import Toast from "react-native-toast-message";

import Header from "../../components/layout/Header";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";
import { ROUTES } from "../../constants/routes";
import authApi from "../../services/authApi";
import { colors, fontSize, spacing } from "../../theme";

const registerSchema = z.object({
  email: z.string().trim().email("Enter a valid email address"),
});

const RegisterScreen = ({ navigation }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { control, handleSubmit } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = async ({ email }) => {
    setIsSubmitting(true);
    try {
      await authApi.register(email.toLowerCase());
      Toast.show({
        type: "success",
        text1: "OTP sent",
      });
      navigation.navigate(ROUTES.AUTH.VERIFY_OTP, { email: email.toLowerCase() });
    } catch (error) {
      if (error?.response?.status === 429) {
        Toast.show({
          type: "error",
          text1: "Too many requests",
          text2: "Please wait before requesting OTP again.",
        });
      } else if (error?.response?.status === 400) {
        Toast.show({
          type: "error",
          text1: "Email already registered",
        });
      } else {
        Toast.show({
          type: "error",
          text1: "Registration failed",
          text2: "Please try again.",
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ScreenWrapper>
      <Header title="Register" subtitle="Create your admission account" />
      <Card>
        <Input
          control={control}
          name="email"
          label="Email"
          placeholder="student@example.com"
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
        />
        <Button title="Send OTP" onPress={handleSubmit(onSubmit)} loading={isSubmitting} />
        <Text style={styles.signInText}>
          Already have an account?{" "}
          <Text onPress={() => navigation.navigate(ROUTES.AUTH.LOGIN)} style={styles.signInLink}>
            Sign in
          </Text>
        </Text>
      </Card>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  signInText: {
    marginTop: spacing.sm,
    color: colors.textSecondary,
    fontSize: fontSize.md,
  },
  signInLink: {
    color: colors.primary,
    fontWeight: "600",
  },
});

export default RegisterScreen;
