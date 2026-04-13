import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import Toast from "react-native-toast-message";

import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Select from "../../components/ui/Select";
import Spinner from "../../components/ui/Spinner";
import INDIAN_STATES from "../../constants/indianStates";
import studentApi from "../../services/studentApi";
import { ROUTES } from "../../constants/routes";
import { colors, fontSize, spacing } from "../../theme";

let DateTimePicker = null;
try {
  DateTimePicker = require("@react-native-community/datetimepicker").default;
} catch {
  DateTimePicker = null;
}

const MIN_AGE = 15;
const MAX_AGE = 30;

const today = new Date();
const minDate = new Date(today.getFullYear() - MAX_AGE, today.getMonth(), today.getDate());
const maxDate = new Date(today.getFullYear() - MIN_AGE, today.getMonth(), today.getDate());

const profileSchema = z
  .object({
    fullName: z.string().trim().min(3, "Full name must be at least 3 characters"),
    dateOfBirth: z.date({
      required_error: "Date of birth is required",
      invalid_type_error: "Date of birth is required",
    }),
    gender: z.enum(["Male", "Female", "Other"], {
      required_error: "Gender is required",
    }),
    mobileNumber: z
      .string()
      .trim()
      .regex(/^[6-9]\d{9}$/, "Enter a valid 10-digit mobile number"),
    street: z.string().trim().min(1, "Street / House No is required"),
    city: z.string().trim().min(1, "City is required"),
    state: z.string().trim().min(1, "State is required"),
    pincode: z.string().trim().regex(/^\d{6}$/, "Pincode must be exactly 6 digits"),
    category: z.enum(["General", "OBC", "SC", "ST"], {
      required_error: "Category is required",
    }),
    domicileState: z.string().trim().min(1, "Domicile state is required"),
  })
  .refine(
    (values) => {
      if (!values.dateOfBirth) {
        return false;
      }
      const dob = new Date(values.dateOfBirth);
      if (Number.isNaN(dob.getTime())) {
        return false;
      }
      const age = today.getFullYear() - dob.getFullYear();
      const hasHadBirthday =
        today.getMonth() > dob.getMonth() ||
        (today.getMonth() === dob.getMonth() && today.getDate() >= dob.getDate());
      const adjustedAge = hasHadBirthday ? age : age - 1;
      return adjustedAge >= MIN_AGE && adjustedAge <= MAX_AGE;
    },
    {
      message: "Age must be between 15 and 30",
      path: ["dateOfBirth"],
    }
  );

const GENDER_OPTIONS = [
  { label: "Male", value: "Male" },
  { label: "Female", value: "Female" },
  { label: "Other", value: "Other" },
];

const CATEGORY_OPTIONS = [
  { label: "General", value: "General" },
  { label: "OBC", value: "OBC" },
  { label: "SC", value: "SC" },
  { label: "ST", value: "ST" },
];

const STATE_OPTIONS = INDIAN_STATES.map((state) => ({ label: state, value: state }));

const formatDate = (dateValue) => {
  if (!dateValue) {
    return "";
  }
  const d = new Date(dateValue);
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const yyyy = d.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
};

const toIsoDate = (dateValue) => {
  const d = new Date(dateValue);
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
};

const parseManualDate = (value) => {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(value.trim());
  if (!match) {
    return null;
  }
  const day = Number(match[1]);
  const month = Number(match[2]);
  const year = Number(match[3]);
  const parsed = new Date(year, month - 1, day);
  if (
    Number.isNaN(parsed.getTime()) ||
    parsed.getDate() !== day ||
    parsed.getMonth() !== month - 1 ||
    parsed.getFullYear() !== year
  ) {
    return null;
  }
  return parsed;
};

const EditProfileScreen = ({ navigation }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [manualDobText, setManualDobText] = useState("");
  const [isLocked, setIsLocked] = useState(false);

  const mobileRef = useRef(null);
  const streetRef = useRef(null);
  const cityRef = useRef(null);
  const pincodeRef = useRef(null);

  const defaultValues = useMemo(
    () => ({
      fullName: "",
      dateOfBirth: null,
      gender: "",
      mobileNumber: "",
      street: "",
      city: "",
      state: "",
      pincode: "",
      category: "",
      domicileState: "",
    }),
    []
  );

  const {
    control,
    handleSubmit,
    setValue,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(profileSchema),
    defaultValues,
  });

  useEffect(() => {
    const loadProfile = async () => {
      setIsLoading(true);
      try {
        const [{ data: profileData }, statusResp] = await Promise.all([
          studentApi.getProfile(),
          studentApi.getStatus().catch(() => ({ data: null })),
        ]);

        const profile = profileData?.profile || profileData || {};
        const statusFromProfile =
          profileData?.application_status || profile?.application_status || null;
        const statusFromStatusApi =
          statusResp?.data?.application_status || statusResp?.data?.status || null;
        const applicationStatus = (statusFromProfile || statusFromStatusApi || "draft")
          .toString()
          .toLowerCase();
        setIsLocked(applicationStatus !== "draft");

        if (profile.full_name) {
          setValue("fullName", profile.full_name);
        }
        if (profile.date_of_birth) {
          const dob = new Date(profile.date_of_birth);
          if (!Number.isNaN(dob.getTime())) {
            setValue("dateOfBirth", dob);
            setManualDobText(formatDate(dob));
          }
        }
        if (profile.gender) {
          setValue("gender", profile.gender);
        }
        if (profile.mobile_number) {
          setValue("mobileNumber", String(profile.mobile_number).replace(/\D/g, "").slice(-10));
        }
        if (profile.address?.street) {
          setValue("street", profile.address.street);
        }
        if (profile.address?.city) {
          setValue("city", profile.address.city);
        }
        if (profile.address?.state) {
          setValue("state", profile.address.state);
        }
        if (profile.address?.pincode) {
          setValue("pincode", String(profile.address.pincode).replace(/\D/g, "").slice(0, 6));
        }
        if (profile.category) {
          setValue("category", profile.category);
        }
        if (profile.domicile_state) {
          setValue("domicileState", profile.domicile_state);
        }
      } catch {
        Toast.show({
          type: "error",
          text1: "Failed to load profile",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, [setValue]);

  const applyServerErrors = (error) => {
    const payload = error?.response?.data;
    if (!payload || typeof payload !== "object") {
      Toast.show({
        type: "error",
        text1: "Profile update failed",
        text2: "Please try again.",
      });
      return;
    }

    const fieldMap = {
      full_name: "fullName",
      date_of_birth: "dateOfBirth",
      gender: "gender",
      mobile_number: "mobileNumber",
      category: "category",
      domicile_state: "domicileState",
      street: "street",
      city: "city",
      state: "state",
      pincode: "pincode",
    };

    Object.entries(payload).forEach(([key, value]) => {
      if (key === "address" && typeof value === "object" && value !== null) {
        Object.entries(value).forEach(([addressKey, addressValue]) => {
          const message = Array.isArray(addressValue) ? addressValue[0] : String(addressValue);
          const mapped = fieldMap[addressKey];
          if (mapped) {
            setError(mapped, { type: "server", message });
          }
        });
      } else {
        const mapped = fieldMap[key];
        const message = Array.isArray(value) ? value[0] : String(value);
        if (mapped) {
          setError(mapped, { type: "server", message });
        }
      }
    });
  };

  const onSubmit = async (values) => {
    if (isLocked) {
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        full_name: values.fullName,
        date_of_birth: toIsoDate(values.dateOfBirth),
        gender: values.gender,
        mobile_number: values.mobileNumber,
        address: {
          street: values.street,
          city: values.city,
          state: values.state,
          pincode: values.pincode,
        },
        category: values.category,
        domicile_state: values.domicileState,
      };
      await studentApi.updateProfile(payload);
      Toast.show({
        type: "success",
        text1: "Profile updated",
      });
      navigation.navigate(ROUTES.HOME.DASHBOARD);
    } catch (error) {
      applyServerErrors(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading || isSubmitting) {
    return <Spinner fullScreen size="large" />;
  }

  return (
    <ScreenWrapper scroll={false} padded={false}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <Pressable onPress={() => navigation.navigate(ROUTES.HOME.DASHBOARD)}>
            <Text style={styles.backLink}>Back to Dashboard</Text>
          </Pressable>
          <Text style={styles.title}>Edit Profile</Text>
          <Text style={styles.subtitle}>Update your details before final submission.</Text>

          {isLocked ? (
            <Card style={styles.lockBanner}>
              <Text style={styles.lockText}>Profile is locked after application submission</Text>
            </Card>
          ) : null}

          <Card>
            <Text style={styles.sectionTitle}>Section 1: Personal Details</Text>

            <Input
              control={control}
              name="fullName"
              label="Full Name"
              placeholder="Rajesh Kumar"
              autoCapitalize="words"
              returnKeyType="next"
              editable={!isLocked}
              onSubmitEditing={() => mobileRef.current?.focus()}
              blurOnSubmit={false}
            />

            <Controller
              control={control}
              name="dateOfBirth"
              render={({ field: { value, onChange } }) => (
                <View style={styles.fieldContainer}>
                  <Text style={styles.label}>Date of Birth</Text>
                  <Pressable
                    style={[
                      styles.dateTrigger,
                      isLocked && styles.disabledBlock,
                      errors.dateOfBirth && styles.dateInputError,
                    ]}
                    onPress={() => {
                      if (!isLocked) {
                        setShowDatePicker(true);
                      }
                    }}
                  >
                    <Text style={[styles.dateText, !value && styles.placeholder]}>
                      {value ? formatDate(value) : "Select date"}
                    </Text>
                  </Pressable>
                  {errors.dateOfBirth ? (
                    <Text style={styles.errorText}>{errors.dateOfBirth.message}</Text>
                  ) : null}
                  {showDatePicker && DateTimePicker ? (
                    <DateTimePicker
                      value={value || maxDate}
                      mode="date"
                      display={Platform.OS === "ios" ? "spinner" : "default"}
                      minimumDate={minDate}
                      maximumDate={maxDate}
                      onChange={(event, selectedDate) => {
                        if (Platform.OS !== "ios") {
                          setShowDatePicker(false);
                        }
                        if (selectedDate) {
                          onChange(selectedDate);
                          setManualDobText(formatDate(selectedDate));
                        }
                      }}
                    />
                  ) : null}
                  {!DateTimePicker ? (
                    <TextInput
                      style={[
                        styles.dateInput,
                        isLocked && styles.disabledBlock,
                        errors.dateOfBirth && styles.dateInputError,
                      ]}
                      editable={!isLocked}
                      placeholder="DD/MM/YYYY"
                      placeholderTextColor={colors.textSecondary}
                      value={manualDobText}
                      keyboardType="number-pad"
                      maxLength={10}
                      onChangeText={(text) => {
                        setManualDobText(text);
                        const parsed = parseManualDate(text);
                        if (parsed) {
                          onChange(parsed);
                        }
                      }}
                    />
                  ) : null}
                </View>
              )}
            />

            <Controller
              control={control}
              name="gender"
              render={({ field: { value, onChange } }) => (
                <Select
                  label="Gender"
                  placeholder="Select gender"
                  options={GENDER_OPTIONS}
                  value={value}
                  onChange={onChange}
                  error={errors.gender?.message}
                  disabled={isLocked}
                />
              )}
            />

            <Input
              control={control}
              name="mobileNumber"
              label="Mobile Number"
              placeholder="9876543210"
              keyboardType="phone-pad"
              maxLength={10}
              returnKeyType="next"
              editable={!isLocked}
              onSubmitEditing={() => streetRef.current?.focus()}
              inputRef={mobileRef}
            />

            <Text style={styles.sectionTitle}>Section 2: Address</Text>

            <Input
              control={control}
              name="street"
              label="Street / House No"
              placeholder="1-2-3, Kukatpally"
              multiline
              editable={!isLocked}
              inputRef={streetRef}
              returnKeyType="next"
              onSubmitEditing={() => cityRef.current?.focus()}
            />

            <Input
              control={control}
              name="city"
              label="City"
              placeholder="Hyderabad"
              returnKeyType="next"
              editable={!isLocked}
              onSubmitEditing={() => pincodeRef.current?.focus()}
              inputRef={cityRef}
            />

            <Controller
              control={control}
              name="state"
              render={({ field: { value, onChange } }) => (
                <Select
                  label="State"
                  placeholder="Select state"
                  options={STATE_OPTIONS}
                  value={value}
                  onChange={onChange}
                  error={errors.state?.message}
                  disabled={isLocked}
                />
              )}
            />

            <Input
              control={control}
              name="pincode"
              label="Pincode"
              placeholder="500072"
              keyboardType="number-pad"
              maxLength={6}
              returnKeyType="done"
              editable={!isLocked}
              inputRef={pincodeRef}
            />

            <Text style={styles.sectionTitle}>Section 3: Category & Domicile</Text>

            <Controller
              control={control}
              name="category"
              render={({ field: { value, onChange } }) => (
                <Select
                  label="Category"
                  placeholder="Select category"
                  options={CATEGORY_OPTIONS}
                  value={value}
                  onChange={onChange}
                  error={errors.category?.message}
                  disabled={isLocked}
                />
              )}
            />

            <Controller
              control={control}
              name="domicileState"
              render={({ field: { value, onChange } }) => (
                <Select
                  label="Domicile State"
                  placeholder="Select domicile state"
                  options={STATE_OPTIONS}
                  value={value}
                  onChange={onChange}
                  error={errors.domicileState?.message}
                  disabled={isLocked}
                />
              )}
            />

            <Button
              title={isLocked ? "Profile Locked" : "Update Profile"}
              onPress={handleSubmit(onSubmit)}
              disabled={isLocked}
            />
          </Card>
        </ScrollView>
      </KeyboardAvoidingView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  flex: { flex: 1 },
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  backLink: {
    color: colors.primary,
    fontWeight: "600",
    marginBottom: spacing.sm,
  },
  title: {
    fontSize: fontSize.xxl,
    color: colors.text,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  subtitle: {
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  lockBanner: {
    backgroundColor: "#EFF6FF",
    borderColor: colors.primaryLight,
    marginBottom: spacing.md,
  },
  lockText: {
    color: colors.primary,
    fontSize: fontSize.md,
    fontWeight: "600",
  },
  sectionTitle: {
    fontSize: fontSize.lg,
    color: colors.text,
    fontWeight: "700",
    marginBottom: spacing.sm,
    marginTop: spacing.sm,
  },
  fieldContainer: {
    marginBottom: spacing.md,
  },
  label: {
    marginBottom: spacing.xs,
    color: colors.textSecondary,
    fontWeight: "600",
    fontSize: fontSize.md,
  },
  dateTrigger: {
    minHeight: 44,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    backgroundColor: colors.surface,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  dateText: {
    fontSize: fontSize.md,
    color: colors.text,
  },
  dateInput: {
    marginTop: spacing.sm,
    minHeight: 44,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    backgroundColor: colors.surface,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    fontSize: fontSize.md,
    color: colors.text,
  },
  dateInputError: {
    borderColor: colors.danger,
  },
  disabledBlock: {
    backgroundColor: colors.disabled,
  },
  placeholder: {
    color: colors.textSecondary,
  },
  errorText: {
    marginTop: spacing.xs,
    color: colors.danger,
    fontSize: fontSize.sm,
  },
});

export default EditProfileScreen;
