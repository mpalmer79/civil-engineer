import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ResponseAttachmentChecklist from "@/components/ResponseAttachmentChecklist";
import type { ResponsePackageAttachment } from "@/lib/api";

const attachment: ResponsePackageAttachment = {
  attachmentId: "ratt_1",
  responsePackageId: "resp_1",
  label: "Draft review-support response summary",
  attachmentType: "review_support_summary",
  sourceType: "response_package",
  sourceId: "resp_1",
  included: true,
  description: "Printable draft.",
};

describe("ResponseAttachmentChecklist", () => {
  it("renders each attachment label", () => {
    render(<ResponseAttachmentChecklist attachments={[attachment]} />);
    expect(
      screen.getByText("Draft review-support response summary"),
    ).toBeInTheDocument();
  });

  it("shows an empty state when there are no attachments", () => {
    render(<ResponseAttachmentChecklist attachments={[]} />);
    expect(
      screen.getByText("No suggested attachments for this draft."),
    ).toBeInTheDocument();
  });
});
