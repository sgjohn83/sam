export const DOCUMENT_TYPES = [
  {
    key: "aadhar",
    label: "Aadhar Card",
    description: "Front and back of your Aadhar card",
    icon: "credit-card",
    acceptedFormats: "JPG, PNG, or PDF",
    tips: [
      "Ensure all 12 digits of Aadhar number are clearly visible",
      "If using photo, avoid glare and shadows",
      "Both front and back can be in single image or PDF",
    ],
  },
  {
    key: "marksheet_10",
    label: "10th Marksheet (SSC)",
    description: "SSC / 10th class marks memo or certificate",
    icon: "file-text",
    acceptedFormats: "JPG, PNG, or PDF",
    tips: [
      "All subject grades and grade points must be visible",
      "Hall ticket number must be readable",
      "If multiple pages, upload as single PDF",
    ],
  },
  {
    key: "marksheet_12",
    label: "12th Marksheet (Intermediate)",
    description: "Intermediate / 12th class marks memo",
    icon: "file-text",
    acceptedFormats: "JPG, PNG, or PDF",
    tips: [
      "Both year marks should be visible",
      "Include all subject columns",
      "If consolidated memo, ensure single clear scan",
    ],
  },
  {
    key: "rank_card",
    label: "Entrance Rank Card",
    description: "EAPCET / EAMCET rank card",
    icon: "award",
    acceptedFormats: "JPG, PNG, or PDF",
    tips: [
      "Rank number must be clearly visible",
      "Hall ticket number must be readable",
      "Category and local area should be visible",
    ],
  },
];
