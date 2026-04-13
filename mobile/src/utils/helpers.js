export const formatDate = (value) => {
  if (!value) {
    return "";
  }
  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return String(value);
  }
};

export const titleCase = (value = "") =>
  value
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
