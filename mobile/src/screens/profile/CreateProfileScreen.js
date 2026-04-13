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
import { useForm, Controller } from "react-hook-form";
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
import useAuth from "../../hooks/useAuth";
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

const profileSchema = z.object({
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
}).refine(
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

const CreateProfileScreen = () => {
  const { completeProfile, refreshUser } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAutofillLoading, setIsAutofillLoading] = useState(true);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [autofilledFields, setAutofilledFields] = useState({});
  const [manualDobText, setManualDobText] = useState("");

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
    const loadAutofill = async () => {
      setIsAutofillLoading(true);
      try {
        const { data } = await studentApi.getAutofill();
        const profile = data?.profile_fields || {};
        const nextAutofilled = {};

        if (profile.full_name) {
          setValue("fullName", profile.full_name);
          nextAutofilled.fullName = true;
        }
        if (profile.date_of_birth) {
          const dob = new Date(profile.date_of_birth);
          if (!Number.isNaN(dob.getTime())) {
            setValue("dateOfBirth", dob);
            setManualDobText(formatDate(dob));
            nextAutofilled.dateOfBirth = true;
          }
        }
        if (profile.gender) {
          setValue("gender", profile.gender);
          nextAutofilled.gender = true;
        }
        if (profile.mobile_number) {
          setValue("mobileNumber", String(profile.mobile_number).replace(/\D/g, "").slice(-10));
          nextAutofilled.mobileNumber = true;
        }
        if (profile.address?.street) {
          setValue("street", profile.address.street);
          nextAutofilled.street = true;
        }
        if (profile.address?.city) {
          setValue("city", profile.address.city);
          nextAutofilled.city = true;
        }
        if (profile.address?.state) {
          setValue("state", profile.address.state);
          nextAutofilled.state = true;
        }
        if (profile.address?.pincode) {
          setValue("pincode", String(profile.address.pincode).replace(/\D/g, "").slice(0, 6));
          nextAutofilled.pincode = true;
        }
        if (profile.category) {
          setValue("category", profile.category);
          nextAutofilled.category = true;
        }
        if (profile.domicile_state) {
          setValue("domicileState", profile.domicile_state);
          nextAutofilled.domicileState = true;
        }

        setAutofilledFields(nextAutofilled);
      } catch {
        // No autofill data is a valid scenario.
      } finally {
        setIsAutofillLoading(false);
      }
    };

    loadAutofill();
  }, [setValue]);

  const applyServerErrors = (error) => {
    const payload = error?.response?.data;
    if (!payload || typeof payload !== "object") {
      Toast.show({
        type: "error",
        text1: "Profile creation failed",
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

    let hasFieldError = false;

    Object.entries(payload).forEach(([key, value]) => {
      const message = Array.isArray(value) ? value[0] : String(value);
      if (key === "address" && typeof value === "object" && value !== null) {
        Object.entries(value).forEach(([addressKey, addressValue]) => {
          const addressMessage = Array.isArray(addressValue)
            ? addressValue[0]
            : String(addressValue);
          const mapped = fieldMap[addressKey];
          if (mapped) {
            setError(mapped, { type: "server", message: addressMessage });
            hasFieldError = true;
          }
        });
      } else {
        const mapped = fieldMap[key];
        if (mapped) {
          setError(mapped, { type: "server", message });
          hasFieldError = true;
        }
      }
    });

    if (!hasFieldError) {
      Toast.show({
        type: "error",
        text1: "Profile creation failed",
      });
    }
  };

  const onSubmit = async (values) => {
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

      await studentApi.createProfile(payload);
      await refreshUser();
      await completeProfile();
      Toast.show({
        type: "success",
        text1: "Profile created",
      });
    } catch (error) {
      applyServerErrors(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitting) {
    return <Spinner fullScreen size="large" />;
  }

  const autoFillText = "Auto-filled from your Aadhar card";

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
          <Text style={styles.title}>Create Your Profile</Text>
          <Text style={styles.subtitle}>Complete profile setup to continue admission flow.</Text>
          {isAutofillLoading ? <Text style={styles.autofillLoading}>Checking OCR autofill...</Text> : null}

          <Card>
            <Text style={styles.sectionTitle}>Section 1: Personal Details</Text>

            <Input
              control={control}
              name="fullName"
              label="Full Name"
              placeholder="Rajesh Kumar"
              autoCapitalize="words"
              returnKeyType="next"
              onSubmitEditing={() => mobileRef.current?.focus()}
              blurOnSubmit={false}
              helperText={autofilledFields.fullName ? autoFillText : undefined}
            />

            <Controller
              control={control}
              name="dateOfBirth"
              render={({ field: { value, onChange } }) => (
                <View style={styles.fieldContainer}>
                  <Text style={styles.label}>Date of Birth</Text>
                  <Pressable style={styles.dateTrigger} onPress={() => setShowDatePicker(true)}>
                    <Text style={[styles.dateText, !value && styles.placeholder]}>
                      {value ? formatDate(value) : "Select date"}
                    </Text>
                  </Pressable>
                  {errors.dateOfBirth ? (
                    <Text style={styles.errorText}>{errors.dateOfBirth.message}</Text>
                  ) : null}
                  {autofilledFields.dateOfBirth ? (
                    <Text style={styles.helperText}>{autoFillText}</Text>
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
                      style={[styles.dateInput, errors.dateOfBirth && styles.dateInputError]}
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
                  helperText={autofilledFields.gender ? autoFillText : undefined}
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
              onSubmitEditing={() => streetRef.current?.focus()}
              inputRef={mobileRef}
              helperText={autofilledFields.mobileNumber ? autoFillText : undefined}
            />

            <Text style={styles.sectionTitle}>Section 2: Address</Text>

            <Input
              control={control}
              name="street"
              label="Street / House No"
              placeholder="1-2-3, Kukatpally"
              multiline
              inputRef={streetRef}
              returnKeyType="next"
              onSubmitEditing={() => cityRef.current?.focus()}
              helperText={autofilledFields.street ? autoFillText : undefined}
            />

            <Input
              control={control}
              name="city"
              label="City"
              placeholder="Hyderabad"
              returnKeyType="next"
              onSubmitEditing={() => pincodeRef.current?.focus()}
              inputRef={cityRef}
              helperText={autofilledFields.city ? autoFillText : undefined}
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
                  helperText={autofilledFields.state ? autoFillText : undefined}
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
              inputRef={pincodeRef}
              helperText={autofilledFields.pincode ? autoFillText : undefined}
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
                  helperText={autofilledFields.category ? autoFillText : undefined}
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
                  helperText={autofilledFields.domicileState ? autoFillText : undefined}
                />
              )}
            />

            <Button title="Create Profile" onPress={handleSubmit(onSubmit)} />
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
  autofillLoading: {
    color: colors.textSecondary,
    fontSize: fontSize.sm,
    marginBottom: spacing.sm,
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
  placeholder: {
    color: colors.textSecondary,
  },
  errorText: {
    marginTop: spacing.xs,
    color: colors.danger,
    fontSize: fontSize.sm,
  },
  helperText: {
    marginTop: spacing.xs,
    color: colors.textSecondary,
    fontSize: fontSize.sm,
  },
});

export default CreateProfileScreen;
