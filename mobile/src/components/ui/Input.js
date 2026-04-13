import React from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";
import { Controller } from "react-hook-form";

import { colors, spacing, fontSize } from "../../theme";

const BaseInput = ({ label, error, helperText, inputRef, ...props }) => (
  <View style={styles.container}>
    {label ? <Text style={styles.label}>{label}</Text> : null}
    <TextInput
      ref={inputRef}
      placeholderTextColor={colors.textSecondary}
      style={[styles.input, props.editable === false && styles.inputDisabled, error && styles.inputError]}
      {...props}
    />
    {error ? <Text style={styles.error}>{error}</Text> : null}
    {!error && helperText ? <Text style={styles.helper}>{helperText}</Text> : null}
  </View>
);

const Input = ({
  control,
  name,
  rules,
  defaultValue = "",
  helperText,
  error,
  inputRef,
  ...props
}) => {
  if (control && name) {
    return (
      <Controller
        control={control}
        name={name}
        rules={rules}
        defaultValue={defaultValue}
        render={({ field: { onChange, onBlur, value }, fieldState }) => (
          <BaseInput
            {...props}
            value={value}
            onChangeText={onChange}
            onBlur={onBlur}
            helperText={helperText}
            error={fieldState.error?.message}
            inputRef={inputRef}
          />
        )}
      />
    );
  }
  return <BaseInput {...props} helperText={helperText} error={error} inputRef={inputRef} />;
};

const styles = StyleSheet.create({
  container: { marginBottom: spacing.md },
  label: {
    marginBottom: spacing.xs,
    color: colors.textSecondary,
    fontWeight: "600",
    fontSize: fontSize.md,
  },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    color: colors.text,
    fontSize: fontSize.md,
  },
  inputDisabled: {
    backgroundColor: colors.disabled,
    color: colors.textSecondary,
  },
  inputError: { borderColor: colors.danger },
  error: { marginTop: spacing.xs, color: colors.danger, fontSize: fontSize.sm },
  helper: { marginTop: spacing.xs, color: colors.textSecondary, fontSize: fontSize.sm },
});

export default Input;
