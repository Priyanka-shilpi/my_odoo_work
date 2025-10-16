{
    "name": "School Management System",
    "author": "Vivek",
    "version": "18.0",
    "license": "LGPL-3",
    "summary": "School Management",
    "category": "Management",
    "description": """A Complete Custom Module for School Management""",
    "company": "Sidmec Technology",
    "depends": ["base", "mail", "hr","board"],

    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/security.xml",



# Data
        "data/send_marks_mail.xml",

        # Core Models
        "views/view_admission.xml",
        "views/bulk_admission.xml",
        "views/View_student.xml",
        "views/view_parent.xml",
        "views/view_teachers.xml",
        "views/view_accountant.xml",
        "views/librarian.xml",
        # Academic
        "views/views_class.xml",
        "views/view_academic_room.xml",
        "views/academic_department.xml",
        "views/view_subject.xml",
        "views/subjectlines.xml",
        "views/syllabus.xml",
        "views/syllabusdetails.xml",
        "views/takeattendance.xml",
        "views/attendance.xml",

        # Exams and Marks
        "views/exam.xml",
        "views/marks.xml",
        "views/mark_details.xml",
        "views/view_send_exam_marks.xml",
        # "views/mark_lines.xml",  # Uncomment if needed

        # Timetable
        "views/routine.xml",
        "views/timetable.xml",

        # Library
        "views/view_book_list.xml",
        "views/bookissue.xml",
        "views/issue.xml",

        # Fees and Finance
        "views/student_feemanager.xml",
        "views/fee_manager.xml",
        "views/mass_invoice.xml",
        "views/expense.xml",
        "views/expense_manager.xml",

        # Transport
        "views/view_driver.xml",
        "views/view_vechicle.xml",
        "views/view_assign_students.xml",
        "views/allocating_students.xml",

        # Attendance
        "views/biometric_attendance.xml",

        # Events & Extras
        "views/events.xml",
        "views/galleryviews.xml",
        "views/alumini_manage.xml",
        "views/online_courses.xml",
        "views/coursedetails.xml",
        "views/grades.xml",
        "views/noticeboard.xml",
        "views/res_partner.xml",

        # Reports
        "report/report.xml",
        "report/report_fee_invoice_template.xml",
        "report/report_student_marks_template.xml",
        "views/view_school_dashboard.xml",
        # Settings & Menus
        "views/school_settings.xml",
        "views/menu.xml",



    ],
}
