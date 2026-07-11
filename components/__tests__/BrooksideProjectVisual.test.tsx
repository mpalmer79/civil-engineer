import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import BrooksideProjectVisual from "@/components/BrooksideProjectVisual";
import { brooksideMedia } from "@/lib/brooksideMedia";

// The single Brookside visual component: every variant must use the
// centralized path, alt text, and caption copy, with a semantic figure and
// figcaption, and the caption must sit outside the image box (below it),
// never over the image.

describe("BrooksideProjectVisual", () => {
  it("renders the feature variant with the centralized alt and disclosure", () => {
    render(<BrooksideProjectVisual variant="feature" />);
    const figure = screen.getByTestId("brookside-project-visual");
    expect(figure.tagName).toBe("FIGURE");
    const image = screen.getByRole("img", { name: brooksideMedia.image.alt });
    expect(image).toBeInTheDocument();
    expect(image.getAttribute("src")).toContain(
      encodeURIComponent(brooksideMedia.image.src),
    );
    expect(screen.getByText(brooksideMedia.disclosure)).toBeInTheDocument();
  });

  it("renders the proof variant with the DXF-distinction caption", () => {
    render(<BrooksideProjectVisual variant="proof" />);
    expect(screen.getByText(brooksideMedia.proofCaption)).toBeInTheDocument();
    expect(
      screen.queryByText(brooksideMedia.disclosure),
    ).not.toBeInTheDocument();
  });

  it("renders the demo-cover variant with the disclosure", () => {
    render(<BrooksideProjectVisual variant="demo-cover" />);
    expect(screen.getByText(brooksideMedia.disclosure)).toBeInTheDocument();
  });

  it("keeps the caption below the image, not over it", () => {
    const { container } = render(<BrooksideProjectVisual variant="feature" />);
    const figure = container.querySelector("figure");
    const caption = container.querySelector("figcaption");
    const imageWrapper = figure?.firstElementChild;
    expect(caption).not.toBeNull();
    // The image lives in the first wrapper; the caption is a following
    // sibling of that wrapper rather than a child positioned inside it.
    expect(imageWrapper?.contains(caption as Node)).toBe(false);
    expect(
      (imageWrapper as Element).compareDocumentPosition(caption as Node) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("renders the card variant as a fill figure with a screen-reader disclosure", () => {
    const { container } = render(<BrooksideProjectVisual variant="card" />);
    const figure = screen.getByTestId("brookside-project-visual");
    expect(figure.dataset.variant).toBe("card");
    expect(
      screen.getByRole("img", { name: brooksideMedia.image.alt }),
    ).toBeInTheDocument();
    const caption = container.querySelector("figcaption");
    expect(caption).toHaveClass("sr-only");
    expect(caption).toHaveTextContent(brooksideMedia.cardDisclosure);
  });

  it("uses intrinsic dimensions on framed variants so layout cannot shift", () => {
    render(<BrooksideProjectVisual variant="feature" />);
    const image = screen.getByRole("img", { name: brooksideMedia.image.alt });
    expect(image).toHaveAttribute("width", String(brooksideMedia.image.width));
    expect(image).toHaveAttribute(
      "height",
      String(brooksideMedia.image.height),
    );
  });
});
