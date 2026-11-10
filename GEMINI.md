# PROJECT UI/UX WORKSPACE RULES — MANDATORY SKILLS USAGE

> **MANDATORY POLICY**: Bất cứ khi nào tác vụ có liên quan đến UI/UX (thiết kế, code giao diện, styling, layout, components, design system, typography, màu sắc, animation, responsive, accessibility, SEO metadata, cải tiến/dọn dẹp giao diện), **BẮT BUỘC PHẢI KÍCH HOẠT VÀ ÁP DỤNG TRIỆT ĐỂ** toàn bộ hệ thống skill đã cài đặt tại `.agents/skills/`. Tuyệt đối không code UI tùy tiện, không để xảy ra AI-generated slop.

---

## 1. HỆ THỐNG SKILL BẮT BUỘC ÁP DỤNG THEO TỪNG GIAI ĐOẠN

### 阶段 1: Khởi Tạo & Quy Hoạch Design System
* **`ui-ux-pro-max` (Bắt buộc chạy công cụ tra cứu offline)**:
  - Trước khi code giao diện mới, phải chạy script reasoning:
    ```bash
    python .agents/skills/ui-ux-pro-max/scripts/design_system.py "<tên_chủ_đề_hoặc_lĩnh_vực>"
    ```
    để lấy chính xác: Bảng màu chuẩn (Primary, Secondary, Accent, Background), Cặp Font Typography, Layout Pattern, Key Effects và Pre-delivery Checklist.
  - Sử dụng search script để tra cứu style, UX guidelines, palette, stack:
    ```bash
    python .agents/skills/ui-ux-pro-max/scripts/search.py "<từ_khóa>"
    ```
* **`design-system` & `ui-styling`**: Thiết lập tokens 3 lớp (primitive → semantic → component), tuân thủ bảng màu và phong cách chuẩn (Minimalism, Bento Grid, Modern SaaS,...).
* **`create-design-md`**: Nếu dự án có sẵn giao diện hoặc cần lưu lại chuẩn UI, chạy skill này để trích xuất và duy trì tài liệu `DESIGN.md`.

---

### 阶段 2: Xây Dựng Component & Viết Code Giao Diện
* **`baseline-ui` (Bắt buộc tuân thủ 100% khi viết code UI)**:
  - **Component Primitives**: Ưu tiên Base UI, Radix UI hoặc component thư viện chuẩn của stack; KHÔNG tự chế lại keyboard navigation hoặc focus states.
  - **Class & Utility**: Dùng Tailwind CSS với `cn` utility (`clsx` + `tailwind-merge`).
  - **Kích thước & Viewport**: Tuyệt đối dùng `h-dvh` thay vì `h-screen`; tuân thủ `safe-area-inset`.
  - **Tương tác**: Toàn bộ icon-only button phải có `aria-label`; tất cả phần tử tương tác phải có `cursor-pointer`. Hành động phá hủy (destructive) bắt buộc dùng `AlertDialog`.
  - **Xử lý Text/Label**: Đảm bảo text không bị cắt cụt (clipping), dùng responsive text wrapping, thẻ chip/tag phải có cơ chế bọc (wrap) hoặc `+n`.
* **`component-canvas` / `create-canvas`**: Khi cần phát triển các component phức tạp hoặc nhiều biến thể (variants), sử dụng canvas để trực quan hóa và kiểm thử trước khi ghép vào layout chính.
* **`ui-skills-root`**: Sử dụng làm tầng routing điều phối khi cần chọn skill hẹp nhất cho tác vụ UI cụ thể.

---

### 阶段 3: Rà Soát, Kiểm Thử & Tối Ưu (Audit & Polish)
* **`improve-ui`**: Khi người dùng yêu cầu review, dọn dẹp hoặc nâng cấp một giao diện đã có, bắt buộc chạy quy trình audit đọc trước - đối chiếu evidence - lên kế hoạch - thực thi, không phá vỡ bản sắc hiện có.
* **`fixing-accessibility`**:
  - Đảm bảo độ tương phản text tối thiểu 4.5:1 (hoặc 7:1 nếu AAA).
  - Đảm bảo điều hướng hoàn toàn bằng bàn phím (Tab, Enter, Escape, Arrow keys).
  - Trạng thái focus (`focus-visible`) phải rõ ràng, độc lập với màu nền.
* **`fixing-motion-performance`**:
  - CHỈ animate compositor properties (`transform`, `opacity`). Tuyệt đối KHÔNG animate layout properties (`width`, `height`, `top`, `left`, `margin`, `padding`).
  - Toàn bộ micro-interaction phản hồi dưới 200ms.
  - Bắt buộc tôn trọng `prefers-reduced-motion`.
* **`fixing-metadata`**: Đảm bảo đầy đủ `title`, `description`, thẻ Open Graph, Twitter card, favicon, JSON-LD cho mọi trang được xuất bản.

---

### 阶段 4: Visual Assets & Tài Liệu Bổ Trợ (Nếu có yêu cầu)
* **`banner-design`**: Khi thiết kế banner, thumbnail, cover hoặc visual assets tiếp thị.
* **`brand`**: Khi thiết lập brand identity, logo voice, visual assets.
* **`slides`**: Khi tạo slide thuyết trình kỹ thuật hoặc báo cáo đề tài dạng HTML/Chart.js.

---

## 2. QUY TRÌNH THỰC THI BẮT BUỘC KHI NHẬN TÁC VỤ UI/UX

```
1. NHẬN YÊU CẦU UI/UX
   ↓
2. TRA CỨU & SINH DESIGN SYSTEM
   • Chạy: python .agents/skills/ui-ux-pro-max/scripts/design_system.py "<chủ_đề>"
   • Tra cứu: python .agents/skills/ui-ux-pro-max/scripts/search.py "<từ_khóa>"
   ↓
3. TRIỂN KHAI CODE THEO BASELINE-UI
   • Tailwind + Accessible Primitives
   • dvh, safe-area, aria-labels, cursor-pointer
   ↓
4. AUDIT & VERIFY
   • Accessibility (contrast 4.5:1, focus, keyboard)
   • Motion Performance (compositor only, reduced-motion)
   • Metadata (SEO / Open Graph)
   ↓
5. HOÀN THÀNH VỚI CHỨNG CỚ THỰC TẾ
```
