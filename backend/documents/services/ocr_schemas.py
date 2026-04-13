from pydantic import BaseModel, Field
from typing import Optional, List

class SubjectResult(BaseModel):
    subject_name: str
    grade: str
    grade_points: int
    grade_points_in_words: str

class InterSubjectMarks(BaseModel):
    subject_name: str
    year_1_marks: Optional[int]
    year_2_marks: Optional[int]
    practical_marks: Optional[int]
    total_marks: int
    max_marks: int

class AadharCard(BaseModel):
    name: str = Field(description="Full name as printed")
    date_of_birth: str = Field(description="DOB in DD/MM/YYYY format")
    gender: str = Field(description="Male or Female")
    aadhar_number: str = Field(description="12-digit Aadhaar number, remove spaces")
    address: str = Field(description="Full address block")
    mobile: Optional[str] = Field(description="10-digit mobile if visible")
    transcript: str = Field(description="Full text transcript of document")

class SSCMarksheet(BaseModel):
    candidate_name: str
    father_name: str
    mother_name: str
    date_of_birth: str
    hall_ticket_no: str
    school_name: str
    board: str
    exam_month_year: str
    medium_of_instruction: str
    subject_results: List[SubjectResult]
    total_grade_points: int
    gpa: float
    result_status: str
    identification_marks: List[str]
    transcript: str

class InterMarksheet(BaseModel):
    candidate_name: str
    father_name: str
    mother_name: str
    hall_ticket_no: str
    college_name: str = Field(description="Inter college name")
    group_name: str = Field(description="e.g., M.P.C, Bi.P.C")
    medium: str
    exam_month_year: str
    part_1_subjects: List[InterSubjectMarks]
    part_2_subjects: List[InterSubjectMarks]
    part_3_subjects: List[InterSubjectMarks]
    grand_total: int
    result_division: str
    final_grade: str
    transcript: str

class RankCard(BaseModel):
    entrance_exam_name: str = Field(description="e.g., APEAPCET")
    hall_ticket_no: str
    candidate_name: str
    father_name: str
    gender: str
    rank: int
    category_rank: Optional[int]
    caste_category: str = Field(description="e.g., BC_B, SC, ST, OC")
    local_area: str = Field(description="AU, SVU, OU, or NL")
    transcript: str

SCHEMA_MAP = {
    'aadhar': AadharCard,
    'marksheet_10': SSCMarksheet,
    'marksheet_12': InterMarksheet,
    'rank_card': RankCard,
}
