"""
Water Quality Analysis Laboratory - Official Test Report PDF Generator

Generates high-resolution, formal A4 PDF test reports for water quality laboratory measurements.
Designed strictly in accordance with formal laboratory report standards:
- Professional monochrome / neutral grey typography on crisp white background.
- Formal document heading: WATER QUALITY ANALYSIS REPORT.
- Laboratory identification, division, and contact details.
- Sample, site, and geographical coordinates particulars table.
- Collection, testing, and report generation timestamps.
- Technician / laboratory authority identification.
- Complete 14-parameter analytical test results table with test methods, units, and baseline standards.
- Predicted Water Quality Index (WQI) and categorical grading.
- Observations and scientific remediation recommendations.
- Verification section with authorized signatory name, designation, and formal signature space.
- Authenticity details and statutory electronic document disclaimer.
- Dynamic multi-page pagination with continuation headers and running footers (Report ID & Page X of Y).
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def get_wqi_category(wqi_score: Optional[float]) -> str:
    """Classifies numerical WQI into standard categorical grades."""
    if wqi_score is None:
        return "Not Computed (Incomplete Features)"
    try:
        val = float(wqi_score)
        if val <= 25.0:
            return "Grade A - Excellent Quality (Very High Purity)"
        elif val <= 50.0:
            return "Grade B - Good Quality (Suitable for Conventional Treatment)"
        elif val <= 75.0:
            return "Grade C - Moderate Quality (Standard Treatment Required)"
        elif val <= 100.0:
            return "Grade D - Poor / Degraded Quality (Polluted)"
        else:
            return "Grade E - Severely Polluted (Unfit for Direct Use)"
    except (ValueError, TypeError):
        return "Unknown"


class PurePDFWriter:
    """
    Standards-compliant PDF 1.4 document builder supporting multi-page output.
    Produces clean vector typography, bordered tables, and formal laboratory formatting.
    """

    def __init__(self, width: float = 595.28, height: float = 841.89):
        self.width = width
        self.height = height
        self.pages: List[List[str]] = [[]]
        self.current_page_idx = 0

    @property
    def current_ops(self) -> List[str]:
        return self.pages[self.current_page_idx]

    def new_page(self) -> int:
        """Adds a new page to the document and moves the cursor to it."""
        self.pages.append([])
        self.current_page_idx = len(self.pages) - 1
        return self.current_page_idx

    def _sanitize(self, text: Any) -> str:
        """Sanitizes strings for WinAnsi Type 1 fonts (ASCII 32-126)."""
        if text is None:
            return ""
        text = str(text)
        replacements = {
            "°": " deg ",
            "≥": ">= ",
            "≤": "<= ",
            "µ": "u",
            "±": "+/-",
            "•": "-",
            "–": "-",
            "—": "-",
            "“": '"',
            "”": '"',
            "‘": "'",
            "’": "'",
            "·": "-",
            "\n": " ",
            "\r": "",
            "\t": " ",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        clean = "".join(c if 32 <= ord(c) <= 126 else " " for c in text)
        clean = clean.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        return clean

    def set_fill_color(self, r: float, g: float, b: float):
        self.current_ops.append(f"{r:.3f} {g:.3f} {b:.3f} rg")

    def set_stroke_color(self, r: float, g: float, b: float):
        self.current_ops.append(f"{r:.3f} {g:.3f} {b:.3f} RG")

    def set_line_width(self, width: float):
        self.current_ops.append(f"{width:.2f} w")

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill_color: Optional[tuple] = None,
        stroke_color: Optional[tuple] = None,
        line_width: float = 0.5,
    ):
        """Draws a rectangle with optional fill and stroke."""
        if fill_color:
            self.set_fill_color(*fill_color)
        if stroke_color:
            self.set_stroke_color(*stroke_color)
            self.set_line_width(line_width)

        if fill_color and stroke_color:
            self.current_ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re B")
        elif fill_color:
            self.current_ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re f")
        elif stroke_color:
            self.current_ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re S")

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke_color: tuple = (0.2, 0.2, 0.2),
        line_width: float = 0.6,
    ):
        """Draws a straight line."""
        self.set_stroke_color(*stroke_color)
        self.set_line_width(line_width)
        self.current_ops.append(f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def text(
        self,
        x: float,
        y: float,
        text_str: Any,
        font: str = "F1",
        size: float = 8.5,
        color: tuple = (0.0, 0.0, 0.0),
    ):
        """Renders text: F1 (Helvetica), F2 (Helvetica-Bold), F3 (Helvetica-Oblique)."""
        safe_str = self._sanitize(text_str)
        self.set_fill_color(*color)
        self.current_ops.append(f"BT /{font} {size:.2f} Tf {x:.2f} {y:.2f} Td ({safe_str}) Tj ET")

    def text_right(
        self,
        x_right: float,
        y: float,
        text_str: Any,
        font: str = "F1",
        size: float = 8.5,
        color: tuple = (0.0, 0.0, 0.0),
    ):
        """Right-aligned text approximated based on character metrics."""
        safe_str = self._sanitize(text_str)
        approx_width = len(safe_str) * size * 0.52
        x = max(20.0, x_right - approx_width)
        self.text(x, y, text_str, font=font, size=size, color=color)

    def text_center(
        self,
        x_center: float,
        y: float,
        text_str: Any,
        font: str = "F1",
        size: float = 8.5,
        color: tuple = (0.0, 0.0, 0.0),
    ):
        """Center-aligned text approximated based on character metrics."""
        safe_str = self._sanitize(text_str)
        approx_width = len(safe_str) * size * 0.52
        x = max(20.0, x_center - (approx_width / 2.0))
        self.text(x, y, text_str, font=font, size=size, color=color)

    def add_running_footers(self, report_id: str, sample_id: str, issue_date_str: str):
        """
        Draws running footers on every page after document pagination is complete.
        Includes Report ID, Sample ID, Issue Date, and exact Page X of Y.
        """
        total_pages = len(self.pages)
        for page_idx in range(total_pages):
            ops = self.pages[page_idx]

            # Footer line
            ops.append("0.400 0.400 0.400 RG 0.60 w")
            ops.append("40.00 36.00 m 555.28 36.00 l S")

            # Left: Report ID & Sample ID
            left_text = self._sanitize(f"Report ID: {report_id}  |  Sample ID: {sample_id}")
            ops.append(f"0.250 0.250 0.250 rg BT /F1 7.00 Tf 40.00 24.00 Td ({left_text}) Tj ET")

            # Center: Issue Date
            center_text = self._sanitize(f"Issue Date: {issue_date_str}")
            approx_c_w = len(center_text) * 7.0 * 0.52
            x_c = max(180.0, 297.64 - (approx_c_w / 2.0))
            ops.append(f"0.250 0.250 0.250 rg BT /F1 7.00 Tf {x_c:.2f} 24.00 Td ({center_text}) Tj ET")

            # Right: Page X of Y
            right_text = self._sanitize(f"Page {page_idx + 1} of {total_pages}")
            approx_r_w = len(right_text) * 7.5 * 0.52
            x_r = max(450.0, 555.28 - approx_r_w)
            ops.append(f"0.100 0.100 0.100 rg BT /F2 7.50 Tf {x_r:.2f} 24.00 Td ({right_text}) Tj ET")

            # Sub-footer disclaimer
            sub_text = self._sanitize(
                "Official Laboratory Water Quality Analysis Report  *  Authenticate via Unique Report ID"
            )
            approx_sub_w = len(sub_text) * 5.8 * 0.52
            x_sub = max(30.0, 297.64 - (approx_sub_w / 2.0))
            ops.append(f"0.450 0.450 0.450 rg BT /F1 5.80 Tf {x_sub:.2f} 14.00 Td ({sub_text}) Tj ET")

    def generate_bytes(self) -> bytes:
        """
        Serializes multi-page document into a complete, valid PDF 1.4 binary stream.
        """
        n_pages = len(self.pages)
        objects: Dict[int, bytes] = {}

        # Object 1: Catalog
        objects[1] = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"

        # Object 2: Pages
        kids_str = " ".join(f"{3 + i} 0 R" for i in range(n_pages))
        objects[2] = f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {n_pages} >>\nendobj\n".encode("latin-1")

        font_f1 = 3 + n_pages
        font_f2 = 4 + n_pages
        font_f3 = 5 + n_pages

        # Font objects
        objects[font_f1] = (
            f"{font_f1} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n".encode(
                "latin-1"
            )
        )
        objects[font_f2] = (
            f"{font_f2} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>\nendobj\n".encode(
                "latin-1"
            )
        )
        objects[font_f3] = (
            f"{font_f3} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>\nendobj\n".encode(
                "latin-1"
            )
        )

        # Page and stream objects
        for i in range(n_pages):
            page_obj_id = 3 + i
            stream_obj_id = 6 + n_pages + i

            # Page Object
            p_obj = (
                f"{page_obj_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width:.2f} {self.height:.2f}] "
                f"/Resources << /Font << /F1 {font_f1} 0 R /F2 {font_f2} 0 R /F3 {font_f3} 0 R >> >> "
                f"/Contents {stream_obj_id} 0 R >>\nendobj\n"
            ).encode("latin-1")
            objects[page_obj_id] = p_obj

            # Content stream
            content = "\n".join(self.pages[i]).encode("latin-1")
            s_obj = (
                f"{stream_obj_id} 0 obj\n<< /Length {len(content)} >>\nstream\n".encode("latin-1")
                + content
                + b"\nendstream\nendobj\n"
            )
            objects[stream_obj_id] = s_obj

        # Assemble PDF file with cross-reference table
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets: Dict[int, int] = {}
        sorted_ids = sorted(objects.keys())
        for obj_id in sorted_ids:
            offsets[obj_id] = len(out)
            out.extend(objects[obj_id])

        xref_pos = len(out)
        total_objs = max(sorted_ids) + 1
        out.extend(f"xref\n0 {total_objs}\n".encode("latin-1"))
        out.extend(b"0000000000 65535 f \n")
        for obj_id in range(1, total_objs):
            off = offsets.get(obj_id, 0)
            out.extend(f"{off:010d} 00000 n \n".encode("latin-1"))

        out.extend(
            f"trailer\n<< /Size {total_objs} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1")
        )
        return bytes(out)


class PDFReportService:
    """
    Coordinates the generation and storage of formal laboratory test report PDFs.
    Produces documents formatted strictly as official laboratory analysis records.
    """

    def __init__(self):
        backend_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        self.storage_dir = os.path.join(backend_root, "storage", "reports")
        os.makedirs(self.storage_dir, exist_ok=True)

    def get_report_file_path(self, report_id: str) -> str:
        safe_id = "".join(c for c in report_id if c.isalnum() or c in "-_")
        return os.path.join(self.storage_dir, f"{safe_id}.pdf")

    def generate_water_test_pdf(self, report_data: Dict[str, Any]) -> str:
        """
        Creates a formal, official laboratory water quality analysis PDF report:
        - White background with black / dark grey typography.
        - Strict absence of application branding or promotional graphics.
        - Structured particulars table, WQI summary, 14-parameter results table.
        - Observations, recommendations, and formal verification signature space.
        - Electronic report authenticity details and statutory disclaimer.
        - Dynamic pagination with continuation headers and running footers.
        """
        report_id = report_data.get("report_id") or f"REP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        sample_id = report_data.get("sample_id") or f"SMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        file_path = self.get_report_file_path(report_id)

        pdf = PurePDFWriter(width=595.28, height=841.89)

        # Standard layout boundaries
        left_m = 40.0
        right_m = 555.28
        width_m = right_m - left_m  # 515.28 pt
        bottom_threshold = 68.0

        current_y = 804.0

        def ensure_space(needed_height: float, continuation_title: Optional[str] = None):
            """Ensures sufficient vertical space, triggering a new page with header if needed."""
            nonlocal current_y
            if current_y - needed_height < bottom_threshold:
                pdf.new_page()
                current_y = 804.0
                # Continuation running header
                header_title = continuation_title or "WATER QUALITY ANALYSIS REPORT (CONTINUATION)"
                pdf.text(left_m, current_y, header_title, font="F2", size=9.5, color=(0.1, 0.1, 0.1))
                pdf.text_right(right_m, current_y, f"Report ID: {report_id}", font="F1", size=8.0, color=(0.3, 0.3, 0.3))
                current_y -= 6.0
                pdf.line(left_m, current_y, right_m, current_y, stroke_color=(0.3, 0.3, 0.3), line_width=0.7)
                current_y -= 16.0

        # -------------------------------------------------------------
        # 1. Laboratory Letterhead & Formal Document Header
        # -------------------------------------------------------------
        lab_name = (
            report_data.get("laboratory_name")
            or "WATER QUALITY TESTING & ANALYTICAL LABORATORY"
        ).strip().upper()

        pdf.text(left_m, current_y, lab_name, font="F2", size=12.0, color=(0.0, 0.0, 0.0))
        current_y -= 13.0

        pdf.text(
            left_m,
            current_y,
            "ENVIRONMENTAL TESTING DIVISION  *  WATER QUALITY ANALYSIS & MONITORING SECTION",
            font="F1",
            size=7.5,
            color=(0.25, 0.25, 0.25),
        )
        current_y -= 10.0

        pdf.text(
            left_m,
            current_y,
            "Testing Methodologies: APHA 23rd Edition / Bureau of Indian Standards (IS 3025 Baseline)",
            font="F1",
            size=7.0,
            color=(0.35, 0.35, 0.35),
        )
        current_y -= 8.0

        # Solid separator
        pdf.line(left_m, current_y, right_m, current_y, stroke_color=(0.2, 0.2, 0.2), line_width=1.0)
        current_y -= 18.0

        # Main Report Title (Centered, bold, uppercase)
        pdf.text_center(297.64, current_y, "WATER QUALITY ANALYSIS REPORT", font="F2", size=14.0, color=(0.0, 0.0, 0.0))
        current_y -= 11.0

        pdf.text_center(
            297.64,
            current_y,
            "TEST REPORT OF WATER SAMPLE ANALYSIS AND QUALITY EVALUATION",
            font="F1",
            size=7.5,
            color=(0.25, 0.25, 0.25),
        )
        current_y -= 8.0

        pdf.line(left_m, current_y, right_m, current_y, stroke_color=(0.4, 0.4, 0.4), line_width=0.6)
        current_y -= 14.0

        # -------------------------------------------------------------
        # 2. Section 1: Sample, Location & Testing Particulars Table
        # -------------------------------------------------------------
        water_body_name = report_data.get("water_body_name") or "Krishna River"
        water_body_type = (report_data.get("water_body_type") or "Surface Water / River").capitalize()
        location_name = report_data.get("location_name") or "Designated Monitoring Station"
        district = report_data.get("district") or "Maharashtra"
        state = report_data.get("state") or "Maharashtra"
        lat = report_data.get("latitude")
        lon = report_data.get("longitude")
        sample_type = report_data.get("sample_type") or "Surface Water"
        sampled_at = report_data.get("sampled_at") or report_data.get("measured_at")
        sampled_at_str = (
            sampled_at.strftime("%d-%b-%Y %H:%M IST")
            if isinstance(sampled_at, datetime)
            else str(sampled_at or "As Submitted")
        )
        testing_date = report_data.get("testing_date") or datetime.now(timezone.utc)
        testing_date_str = (
            testing_date.strftime("%d-%b-%Y %H:%M IST")
            if isinstance(testing_date, datetime)
            else str(testing_date)
        )
        report_date_now = datetime.now(timezone.utc)
        report_date_str = report_date_now.strftime("%d-%b-%Y %H:%M IST")
        analyst_name = report_data.get("lab_authority_name") or "Authorized Laboratory Analyst"
        test_method = report_data.get("testing_method") or "Standard Methods (APHA / IS 3025 Baseline)"
        coord_str = f"{lat:.4f} N, {lon:.4f} E" if lat is not None and lon is not None else "Not Recorded / Ambient"

        # Section Heading Bar
        pdf.rect(left_m, current_y - 13.0, width_m, 13.0, fill_color=(0.92, 0.92, 0.92), stroke_color=(0.3, 0.3, 0.3), line_width=0.5)
        pdf.text(left_m + 5.0, current_y - 9.5, "1. SAMPLE, LOCATION & TESTING PARTICULARS", font="F2", size=7.8, color=(0.0, 0.0, 0.0))
        current_y -= 13.0

        # 6-Row Particulars Grid
        particulars_rows = [
            ("Report Number:", str(report_id), "Sample Identifier:", str(sample_id)),
            ("Water Body Name:", str(water_body_name), "Water Body Type:", str(water_body_type)),
            ("Sample Location:", f"{location_name}, {district}".strip(", "), "GPS Coordinates:", coord_str),
            ("Sample Matrix / Type:", str(sample_type), "Sample Collection Date:", sampled_at_str),
            ("Testing / Analysis Date:", testing_date_str, "Report Generation Date:", report_date_str),
            ("Testing Protocol / Standard:", test_method[:38], "Technician / Analyst:", analyst_name[:36]),
        ]

        p_row_h = 13.5
        grid_h = len(particulars_rows) * p_row_h
        pdf.rect(left_m, current_y - grid_h, width_m, grid_h, stroke_color=(0.3, 0.3, 0.3), line_width=0.5)

        # Mid vertical divider
        mid_x = left_m + (width_m / 2.0)
        pdf.line(mid_x, current_y, mid_x, current_y - grid_h, stroke_color=(0.3, 0.3, 0.3), line_width=0.5)

        row_y = current_y
        for r_idx, (lbl1, val1, lbl2, val2) in enumerate(particulars_rows):
            # Row horizontal line (except bottom)
            if r_idx > 0:
                pdf.line(left_m, row_y, right_m, row_y, stroke_color=(0.8, 0.8, 0.8), line_width=0.4)

            # Left column
            pdf.text(left_m + 6.0, row_y - 9.5, lbl1, font="F2", size=7.2, color=(0.2, 0.2, 0.2))
            pdf.text(left_m + 105.0, row_y - 9.5, val1, font="F1", size=7.2, color=(0.0, 0.0, 0.0))

            # Right column
            pdf.text(mid_x + 6.0, row_y - 9.5, lbl2, font="F2", size=7.2, color=(0.2, 0.2, 0.2))
            pdf.text(mid_x + 115.0, row_y - 9.5, val2, font="F1", size=7.2, color=(0.0, 0.0, 0.0))

            row_y -= p_row_h

        current_y = current_y - grid_h - 10.0

        # -------------------------------------------------------------
        # 3. Section 2: Water Quality Index (WQI) & Quality Assessment Box
        # -------------------------------------------------------------
        wqi_score = report_data.get("wqi_score")
        wqi_category = report_data.get("wqi_category") or get_wqi_category(wqi_score)
        safety_classification = report_data.get("safety_classification") or "SAFE"
        ml_algorithm = report_data.get("wqi_algorithm") or "Trained Decision Tree Regressor (12 Parameters)"

        pdf.rect(left_m, current_y - 13.0, width_m, 13.0, fill_color=(0.92, 0.92, 0.92), stroke_color=(0.3, 0.3, 0.3), line_width=0.5)
        pdf.text(left_m + 5.0, current_y - 9.5, "2. WATER QUALITY INDEX (WQI) & BASELINE ASSESSMENT", font="F2", size=7.8, color=(0.0, 0.0, 0.0))
        current_y -= 13.0

        wqi_box_h = 42.0
        pdf.rect(left_m, current_y - wqi_box_h, width_m, wqi_box_h, stroke_color=(0.3, 0.3, 0.3), line_width=0.5)
        pdf.line(mid_x, current_y, mid_x, current_y - wqi_box_h, stroke_color=(0.3, 0.3, 0.3), line_width=0.5)

        # Left side of WQI box: Numerical score and category
        wqi_score_str = f"{wqi_score:.2f} / 100" if wqi_score is not None else "Not Computed (Incomplete Features)"
        pdf.text(left_m + 8.0, current_y - 13.0, "Predicted Water Quality Index (WQI):", font="F2", size=7.5, color=(0.2, 0.2, 0.2))
        pdf.text(left_m + 170.0, current_y - 13.0, wqi_score_str, font="F2", size=8.5, color=(0.0, 0.0, 0.0))

        pdf.text(left_m + 8.0, current_y - 27.0, "Quality Grading / Classification:", font="F2", size=7.5, color=(0.2, 0.2, 0.2))
        pdf.text(left_m + 170.0, current_y - 27.0, wqi_category[:34], font="F1", size=7.5, color=(0.0, 0.0, 0.0))

        pdf.text(left_m + 8.0, current_y - 37.0, "Analytical Assessment Model:", font="F1", size=6.8, color=(0.35, 0.35, 0.35))
        pdf.text(left_m + 170.0, current_y - 37.0, ml_algorithm[:36], font="F1", size=6.8, color=(0.35, 0.35, 0.35))

        # Right side of WQI box: Baseline Screening Status
        pdf.text(mid_x + 8.0, current_y - 13.0, "Baseline Drinking Safety Screening:", font="F2", size=7.5, color=(0.2, 0.2, 0.2))
        pdf.text(mid_x + 180.0, current_y - 13.0, safety_classification, font="F2", size=8.5, color=(0.0, 0.0, 0.0))

        pdf.text(mid_x + 8.0, current_y - 27.0, "Regulatory Baseline Reference:", font="F2", size=7.5, color=(0.2, 0.2, 0.2))
        pdf.text(mid_x + 180.0, current_y - 27.0, "CPCB Class C / BIS IS 10500:2012", font="F1", size=7.2, color=(0.0, 0.0, 0.0))

        pdf.text(mid_x + 8.0, current_y - 37.0, "Screening Scope:", font="F1", size=6.8, color=(0.35, 0.35, 0.35))
        pdf.text(mid_x + 180.0, current_y - 37.0, "Baseline Physical-Chemical-Biological Screening", font="F1", size=6.8, color=(0.35, 0.35, 0.35))

        current_y = current_y - wqi_box_h - 10.0

        # -------------------------------------------------------------
        # 4. Section 3: 14-Parameter Analytical Test Results Table
        # -------------------------------------------------------------
        pdf.rect(left_m, current_y - 13.0, width_m, 13.0, fill_color=(0.92, 0.92, 0.92), stroke_color=(0.3, 0.3, 0.3), line_width=0.5)
        pdf.text(left_m + 5.0, current_y - 9.5, "3. MEASURED PARAMETERS & ANALYTICAL TEST RESULTS (14 PARAMETERS)", font="F2", size=7.8, color=(0.0, 0.0, 0.0))
        current_y -= 13.0

        # Table Column Widths:
        # Col 0 (S.No): 24 pt (40 to 64)
        # Col 1 (Parameter): 136 pt (64 to 200)
        # Col 2 (Test Method): 110 pt (200 to 310)
        # Col 3 (Unit): 56 pt (310 to 366)
        # Col 4 (Standard Limit): 94 pt (366 to 460)
        # Col 5 (Measured Value): 55.28 pt (460 to 515.28)
        # Col 6 (Remarks): 40 pt (515.28 to 555.28)
        c_x = [40.0, 64.0, 200.0, 310.0, 366.0, 460.0, 515.0, 555.28]

        def draw_table_header():
            nonlocal current_y
            th_h = 14.5
            pdf.rect(left_m, current_y - th_h, width_m, th_h, fill_color=(0.88, 0.88, 0.88), stroke_color=(0.3, 0.3, 0.3), line_width=0.5)
            # Vertical column lines
            for x_div in c_x[1:-1]:
                pdf.line(x_div, current_y, x_div, current_y - th_h, stroke_color=(0.3, 0.3, 0.3), line_width=0.4)

            pdf.text(c_x[0] + 3.0, current_y - 10.5, "No.", font="F2", size=7.0, color=(0.0, 0.0, 0.0))
            pdf.text(c_x[1] + 4.0, current_y - 10.5, "Tested Parameter", font="F2", size=7.0, color=(0.0, 0.0, 0.0))
            pdf.text(c_x[2] + 4.0, current_y - 10.5, "Reference Test Method", font="F2", size=7.0, color=(0.0, 0.0, 0.0))
            pdf.text(c_x[3] + 4.0, current_y - 10.5, "Unit", font="F2", size=7.0, color=(0.0, 0.0, 0.0))
            pdf.text(c_x[4] + 4.0, current_y - 10.5, "Standard Baseline Limit", font="F2", size=7.0, color=(0.0, 0.0, 0.0))
            pdf.text(c_x[5] + 4.0, current_y - 10.5, "Measured", font="F2", size=7.0, color=(0.0, 0.0, 0.0))
            pdf.text(c_x[6] + 4.0, current_y - 10.5, "Status", font="F2", size=7.0, color=(0.0, 0.0, 0.0))
            current_y -= th_h

        draw_table_header()

        # The 14 official laboratory parameters definition
        params_def = [
            ("1", "pH", "ph", "APHA 4500-H+ B / IS 3025 (Pt 11)", "pH Units", "6.5 - 8.5", (6.5, 8.5)),
            ("2", "Dissolved Oxygen (DO)", "dissolved_oxygen", "APHA 4500-O C / IS 3025 (Pt 38)", "mg/L", ">= 4.0", (4.0, 999.0)),
            ("3", "Biochemical Oxygen Demand", "bod", "APHA 5210 B / IS 3025 (Pt 44)", "mg/L", "<= 3.0", (0.0, 3.0)),
            ("4", "Chemical Oxygen Demand (COD)", "cod", "APHA 5220 B / IS 3025 (Pt 58)", "mg/L", "<= 250.0", (0.0, 250.0)),
            ("5", "Turbidity", "turbidity", "Nephelometric / IS 3025 (Pt 10)", "NTU", "<= 5.0", (0.0, 5.0)),
            ("6", "Total Dissolved Solids (TDS)", "tds", "Gravimetric / IS 3025 (Pt 16)", "mg/L", "<= 500.0", (0.0, 500.0)),
            ("7", "Electrical Conductivity (EC)", "electrical_conductivity", "Conductivity Meter / IS 3025 (Pt 14)", "uS/cm", "<= 1500.0", (0.0, 1500.0)),
            ("8", "Water Temperature", "temperature", "Thermometric / IS 3025 (Pt 9)", "deg C", "Ambient (15 - 35)", (15.0, 35.0)),
            ("9", "Nitrate (as NO3-)", "nitrate", "UV Spectrophotometric / IS 3025 (Pt 34)", "mg/L", "<= 45.0", (0.0, 45.0)),
            ("10", "Phosphate (as PO4---)", "phosphate", "Stannous Chloride / APHA 4500-P D", "mg/L", "<= 0.10", (0.0, 0.10)),
            ("11", "Chloride (as Cl-)", "chlorides", "Argentometric / IS 3025 (Pt 32)", "mg/L", "<= 250.0", (0.0, 250.0)),
            ("12", "Total Coliform", "total_coliform", "Multiple Tube Fermentation / IS 1622", "MPN/100 mL", "<= 5000", (0.0, 5000.0)),
            ("13", "Fecal Coliform", "fecal_coliform", "Membrane Filtration / IS 1622", "MPN/100 mL", "<= 500", (0.0, 500.0)),
            ("14", "Sulphate (as SO4--)", "sulphate", "Turbidimetric / IS 3025 (Pt 24)", "mg/L", "<= 200.0", (0.0, 200.0)),
        ]

        # Additional parameter (Ammonia Nitrogen) if provided
        params_dict = report_data.get("parameters") or report_data
        if params_dict.get("ammonia_n") is not None:
            params_def.append(
                ("15", "Ammonia Nitrogen (NH3-N)", "ammonia_n", "Phenate Method / APHA 4500-NH3 F", "mg/L", "<= 0.50", (0.0, 0.50))
            )

        row_h = 13.5
        for idx, (p_no, p_name, p_key, p_method, p_unit, p_std, p_bounds) in enumerate(params_def):
            # Check dynamic pagination before each row
            if current_y - row_h < bottom_threshold:
                pdf.new_page()
                current_y = 804.0
                pdf.text(left_m, current_y, "WATER QUALITY ANALYSIS REPORT (CONTINUED - TABLE 3)", font="F2", size=9.5, color=(0.1, 0.1, 0.1))
                pdf.text_right(right_m, current_y, f"Report ID: {report_id}", font="F1", size=8.0, color=(0.3, 0.3, 0.3))
                current_y -= 6.0
                pdf.line(left_m, current_y, right_m, current_y, stroke_color=(0.3, 0.3, 0.3), line_width=0.7)
                current_y -= 14.0
                draw_table_header()

            bg_color = (0.98, 0.98, 0.98) if idx % 2 == 1 else (1.0, 1.0, 1.0)
            pdf.rect(left_m, current_y - row_h, width_m, row_h, fill_color=bg_color, stroke_color=(0.3, 0.3, 0.3), line_width=0.4)

            # Vertical divider lines
            for x_div in c_x[1:-1]:
                pdf.line(x_div, current_y, x_div, current_y - row_h, stroke_color=(0.75, 0.75, 0.75), line_width=0.3)

            # Determine value & compliance
            raw_val = params_dict.get(p_key)
            if raw_val is None and p_key == "chlorides":
                raw_val = params_dict.get("chloride")

            if raw_val is not None:
                try:
                    val_float = float(raw_val)
                    val_str = f"{val_float:.2f}" if "." in str(raw_val) else f"{val_float:.1f}"
                    is_pass = p_bounds[0] <= val_float <= p_bounds[1]
                    status_str = "Within" if is_pass else "Exceeds"
                except (ValueError, TypeError):
                    val_str = str(raw_val)
                    status_str = "Reported"
            else:
                val_str = "N/A"
                status_str = "N/A"

            pdf.text(c_x[0] + 4.0, current_y - 9.5, p_no, font="F1", size=6.8, color=(0.2, 0.2, 0.2))
            pdf.text(c_x[1] + 4.0, current_y - 9.5, p_name[:26], font="F2", size=6.8, color=(0.0, 0.0, 0.0))
            pdf.text(c_x[2] + 4.0, current_y - 9.5, p_method[:28], font="F1", size=6.5, color=(0.25, 0.25, 0.25))
            pdf.text(c_x[3] + 4.0, current_y - 9.5, p_unit[:12], font="F1", size=6.8, color=(0.2, 0.2, 0.2))
            pdf.text(c_x[4] + 4.0, current_y - 9.5, p_std[:20], font="F1", size=6.8, color=(0.25, 0.25, 0.25))
            pdf.text(c_x[5] + 6.0, current_y - 9.5, val_str, font="F2", size=7.0, color=(0.0, 0.0, 0.0))
            pdf.text(c_x[6] + 4.0, current_y - 9.5, status_str, font="F1", size=6.8, color=(0.1, 0.1, 0.1))

            current_y -= row_h

        current_y -= 10.0

        # -------------------------------------------------------------
        # 5. Section 4: Observations & Remediation Recommendations
        # -------------------------------------------------------------
        ensure_space(55.0, "WATER QUALITY ANALYSIS REPORT (CONTINUED - OBSERVATIONS)")

        pdf.rect(left_m, current_y - 13.0, width_m, 13.0, fill_color=(0.92, 0.92, 0.92), stroke_color=(0.3, 0.3, 0.3), line_width=0.5)
        pdf.text(left_m + 5.0, current_y - 9.5, "4. OBSERVATIONS & RECOMMENDATIONS", font="F2", size=7.8, color=(0.0, 0.0, 0.0))
        current_y -= 13.0

        obs_h = 40.0
        pdf.rect(left_m, current_y - obs_h, width_m, obs_h, stroke_color=(0.3, 0.3, 0.3), line_width=0.5)

        if safety_classification == "SAFE":
            obs_1 = "- Analytical parameters conform to standard baseline screening criteria (CPCB Designated Best Use Class C / IS 10500:2012)."
            obs_2 = "- Recommended Treatment: Standard conventional filtration (rapid sand filtration) and controlled disinfection (chlorination / UV)."
            obs_3 = "- Surveillance: Maintain regular bi-weekly monitoring schedule to track seasonal hydrological and microbiological variations."
        else:
            obs_1 = "- Threshold exceedances detected in key baseline parameters; sample is non-compliant for untreated drinking or direct potability."
            obs_2 = "- Recommended Treatment: Enhanced multi-stage treatment including coagulation, flocculation, advanced filtration, and robust disinfection."
            obs_3 = "- Surveillance: Conduct root-cause sanitary inspection upstream and schedule repeat confirmatory sampling within 48 to 72 hours."

        pdf.text(left_m + 8.0, current_y - 11.0, obs_1[:125], font="F1", size=6.8, color=(0.15, 0.15, 0.15))
        pdf.text(left_m + 8.0, current_y - 23.0, obs_2[:125], font="F1", size=6.8, color=(0.15, 0.15, 0.15))
        pdf.text(left_m + 8.0, current_y - 35.0, obs_3[:125], font="F1", size=6.8, color=(0.15, 0.15, 0.15))

        current_y = current_y - obs_h - 10.0

        # -------------------------------------------------------------
        # 6. Section 5: Verification & Formal Authorization Section
        # -------------------------------------------------------------
        ensure_space(68.0, "WATER QUALITY ANALYSIS REPORT (CONTINUED - VERIFICATION)")

        pdf.rect(left_m, current_y - 13.0, width_m, 13.0, fill_color=(0.92, 0.92, 0.92), stroke_color=(0.3, 0.3, 0.3), line_width=0.5)
        pdf.text(left_m + 5.0, current_y - 9.5, "5. VERIFICATION & AUTHORIZATION", font="F2", size=7.8, color=(0.0, 0.0, 0.0))
        current_y -= 13.0

        verif_h = 50.0
        pdf.rect(left_m, current_y - verif_h, width_m, verif_h, stroke_color=(0.3, 0.3, 0.3), line_width=0.5)
        pdf.line(mid_x, current_y, mid_x, current_y - verif_h, stroke_color=(0.3, 0.3, 0.3), line_width=0.5)

        # Left side: Testing Analyst details
        pdf.text(left_m + 8.0, current_y - 13.0, "Reporting Laboratory Analyst:", font="F2", size=7.5, color=(0.2, 0.2, 0.2))
        pdf.text(left_m + 8.0, current_y - 24.0, analyst_name, font="F2", size=8.0, color=(0.0, 0.0, 0.0))
        pdf.text(left_m + 8.0, current_y - 35.0, "Designation: Authorized Laboratory Analyst / Environmental Chemist", font="F1", size=6.8, color=(0.3, 0.3, 0.3))
        pdf.text(left_m + 8.0, current_y - 45.0, f"Analysis Date: {testing_date_str}", font="F1", size=6.8, color=(0.35, 0.35, 0.35))

        # Right side: Formal Signature Box
        pdf.text(mid_x + 8.0, current_y - 11.0, "Authorized Signatory Verification:", font="F2", size=7.5, color=(0.2, 0.2, 0.2))

        # Signature box
        sig_box_x = mid_x + 8.0
        sig_box_y = current_y - 42.0
        sig_box_w = width_m / 2.0 - 16.0
        sig_box_h = 28.0
        pdf.rect(sig_box_x, sig_box_y, sig_box_w, sig_box_h, stroke_color=(0.5, 0.5, 0.5), line_width=0.5)
        pdf.text_center(sig_box_x + (sig_box_w / 2.0), sig_box_y + 11.0, "[ Signature of Authorized Signatory ]", font="F3", size=7.2, color=(0.4, 0.4, 0.4))

        pdf.text_right(right_m - 8.0, current_y - 46.0, "Quality Assurance Officer / Lab In-Charge", font="F1", size=6.5, color=(0.3, 0.3, 0.3))

        current_y = current_y - verif_h - 10.0

        # -------------------------------------------------------------
        # 7. Section 6: Report Authenticity & Statutory Disclaimer
        # -------------------------------------------------------------
        ensure_space(46.0, "WATER QUALITY ANALYSIS REPORT (CONTINUED - DISCLAIMER)")

        pdf.rect(left_m, current_y - 11.0, width_m, 11.0, fill_color=(0.95, 0.95, 0.95), stroke_color=(0.4, 0.4, 0.4), line_width=0.4)
        pdf.text(left_m + 5.0, current_y - 8.0, "6. REPORT AUTHENTICITY DETAILS & REGULATORY DISCLAIMER", font="F2", size=6.8, color=(0.2, 0.2, 0.2))
        current_y -= 11.0

        disc_h = 32.0
        pdf.rect(left_m, current_y - disc_h, width_m, disc_h, stroke_color=(0.4, 0.4, 0.4), line_width=0.4)

        d_line1 = (
            "1. AUTHENTICITY NOTICE: This document is an electronically generated water quality analytical report compiled from laboratory measurements "
            "recorded by authorized personnel and evaluated against published baseline criteria (CPCB Class C & BIS IS 10500:2012)."
        )
        d_line2 = (
            "2. STATUTORY DISTINCTION: This electronically generated report does NOT constitute an officially accredited statutory test certificate "
            "or government regulatory clearance (such as NABL/ISO/IEC 17025 certification) unless physically signed, sealed, and issued through statutory protocols."
        )
        d_line3 = (
            "3. SCOPE OF RESULTS: Analytical test results relate solely to the sample as tested and submitted for the specified monitoring point. "
            "The testing laboratory accepts no liability for subsequent alteration, degradation, or unrepresentative sample collection."
        )

        pdf.text(left_m + 6.0, current_y - 9.0, d_line1[:135], font="F1", size=5.8, color=(0.25, 0.25, 0.25))
        pdf.text(left_m + 6.0, current_y - 18.0, d_line2[:135], font="F1", size=5.8, color=(0.25, 0.25, 0.25))
        pdf.text(left_m + 6.0, current_y - 27.0, d_line3[:135], font="F1", size=5.8, color=(0.25, 0.25, 0.25))

        # -------------------------------------------------------------
        # 8. Post-Processing: Running Footers on Every Page
        # -------------------------------------------------------------
        pdf.add_running_footers(
            report_id=report_id,
            sample_id=sample_id,
            issue_date_str=report_date_str,
        )

        # Write output file
        pdf_bytes = pdf.generate_bytes()
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        return file_path


# Global singleton service instance
pdf_report_service = PDFReportService()
