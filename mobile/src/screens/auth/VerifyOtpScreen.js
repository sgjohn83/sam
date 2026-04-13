import React, { useEffect, useRef, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import Toast from "react-native-toast-message";

import Header from "../../components/layout/Header";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import useAuth from "../../hooks/useAuth";
import authApi from "../../services/authApi";
import { colors, fontSize, spacing } from "../../theme";

const OTP_LENGTH = 6;
const RESEND_SECONDS = 60;

const VerifyOtpScreen = ({ route }) => {
  const email = route?.params?.email || "";
  const { login } = useAuth();
  const [digits, setDigits] = useState(Array(OTP_LENGTH).fill(""));
  const [isVerifying, setIsVerifying] = useState(false);
  const [attemptMessage, setAttemptMessage] = useState("");
  const [resendCountdown, setResendCountdown] = useState(RESEND_SECONDS);
  const inputRefs = useRef([]);

  useEffect(() => {
    const timer = setInterval(() => {
      setResendCountdown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const code = digits.join("");

  const submitOtp = async (finalCode) => {
    if (isVerifying || finalCode.length !== OTP_LENGTH || !email) {
      return;
    }
    setIsVerifying(true);
    setAttemptMessage("");
    try {
      const { data } = await authApi.verifyOtp({ email, code: finalCode });
      await login(data.token, data.user);
    } catch (error) {
      const message = error?.response?.data?.error || "OTP verification failed";
      if (message.toLowerCase().includes("attempt")) {
        setAttemptMessage(message);
      }
      Toast.show({
        type: "error",
        text1: "Verification failed",
        text2: message,
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleDigitChange = (value, index) => {
    const onlyNumber = value.replace(/\D/g, "");
    const nextDigits = [...digits];
    nextDigits[index] = onlyNumber.slice(-1);
    setDigits(nextDigits);

    if (onlyNumber && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }

    const finalCode = nextDigits.join("");
    if (finalCode.length === OTP_LENGTH && !nextDigits.includes("")) {
      submitOtp(finalCode);
    }
  };

  const handleKeyPress = (event, index) => {
    if (event.nativeEvent.key === "Backspace" && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleResend = async () => {
    if (!email || resendCountdown > 0) {
      return;
    }
    try {
      await authApi.register(email);
      setResendCountdown(RESEND_SECONDS);
      Toast.show({
        type: "success",
        text1: "OTP sent",
      });
    } catch (error) {
      const statusCode = error?.response?.status;
      const message =
        statusCode === 429
          ? "Too many requests, try again later."
          : error?.response?.data?.error || "Failed to resend OTP.";
      Toast.show({
        type: "error",
        text1: "Resend failed",
        text2: message,
      });
    }
  };

  return (
    <ScreenWrapper>
      <Header title="Verify OTP" subtitle="Enter the 6-digit code sent to your email" />
      <Card>
        <Text style={styles.emailLabel}>Email</Text>
        <Text style={styles.emailValue}>{email || "No email provided"}</Text>

        <View style={styles.otpRow}>
          {digits.map((digit, index) => (
            <TextInput
              key={`otp-${index}`}
              ref={(ref) => {
                inputRefs.current[index] = ref;
              }}
              value={digit}
              style={styles.otpInput}
              onChangeText={(text) => handleDigitChange(text, index)}
              onKeyPress={(event) => handleKeyPress(event, index)}
              maxLength={1}
              keyboardType="number-pad"
              textAlign="center"
              autoFocus={index === 0}
            />
          ))}
        </View>

        {attemptMessage ? <Text style={styles.attemptText}>{attemptMessage}</Text> : null}

        <Button title="Verify" onPress={() => submitOtp(code)} loading={isVerifying} />

        <View style={styles.resendContainer}>
          {resendCountdown > 0 ? (
            <Text style={styles.resendCountdown}>Resend in {resendCountdown}s</Text>
          ) : (
            <Pressable onPress={handleResend}>
              <Text style={styles.resendLink}>Resend OTP</Text>
            </Pressable>
          )}
        </View>

        <Text style={styles.note}>Code valid for 10 minutes.</Text>
      </Card>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  emailLabel: {
    color: colors.textSecondary,
    fontSize: fontSize.sm,
    marginBottom: spacing.xs,
  },
  emailValue: {
    color: colors.text,
    fontSize: fontSize.md,
    fontWeight: "600",
    marginBottom: spacing.md,
  },
  otpRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  otpInput: {
    width: 44,
    height: 52,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    backgroundColor: colors.surface,
    fontSize: fontSize.lg,
    color: colors.text,
    fontWeight: "700",
  },
  attemptText: {
    color: colors.warning,
    fontSize: fontSize.sm,
    marginBottom: spacing.sm,
  },
  resendContainer: {
    alignItems: "center",
    marginTop: spacing.md,
  },
  resendCountdown: {
    color: colors.textSecondary,
    fontSize: fontSize.md,
  },
  resendLink: {
    color: colors.primary,
    fontSize: fontSize.md,
    fontWeight: "600",
  },
  note: {
    marginTop: spacing.sm,
    color: colors.textSecondary,
    textAlign: "center",
  },
});

export default VerifyOtpScreen;
