// Default categories. Lao names are a first draft - please check them.
export type CategoryKind = "expense" | "income";

export interface Category {
  slug: string;
  en: string;
  lo: string;
  emoji: string;
  kind: CategoryKind;
}

export const CATEGORIES: Category[] = [
  { slug: "food", en: "Food & drinks", lo: "ອາຫານ ແລະ ເຄື່ອງດື່ມ", emoji: "🍜", kind: "expense" },
  { slug: "groceries", en: "Groceries & market", lo: "ຕະຫຼາດ ແລະ ເຄື່ອງກິນເຄື່ອງໃຊ້", emoji: "🛒", kind: "expense" },
  { slug: "transport", en: "Transport & fuel", lo: "ການເດີນທາງ ແລະ ນ້ຳມັນ", emoji: "🛵", kind: "expense" },
  { slug: "shopping", en: "Shopping", lo: "ຊື້ເຄື່ອງ", emoji: "🛍️", kind: "expense" },
  { slug: "bills", en: "Bills & utilities", lo: "ຄ່ານ້ຳ ຄ່າໄຟ ແລະ ບໍລິການ", emoji: "💡", kind: "expense" },
  { slug: "phone_internet", en: "Phone & internet", lo: "ໂທລະສັບ ແລະ ອິນເຕີເນັດ", emoji: "📱", kind: "expense" },
  { slug: "health", en: "Health", lo: "ສຸຂະພາບ", emoji: "💊", kind: "expense" },
  { slug: "education", en: "Education", lo: "ການສຶກສາ", emoji: "📚", kind: "expense" },
  { slug: "family", en: "Family", lo: "ຄອບຄົວ", emoji: "👨‍👩‍👧", kind: "expense" },
  { slug: "people", en: "Transfers to people", lo: "ໂອນໃຫ້ຄົນອື່ນ", emoji: "🤝", kind: "expense" },
  { slug: "entertainment", en: "Entertainment", lo: "ບັນເທີງ", emoji: "🎬", kind: "expense" },
  { slug: "other", en: "Other", lo: "ອື່ນໆ", emoji: "📦", kind: "expense" },
  { slug: "salary", en: "Salary", lo: "ເງິນເດືອນ", emoji: "💼", kind: "income" },
  { slug: "income_other", en: "Other income", lo: "ລາຍຮັບອື່ນ", emoji: "💰", kind: "income" },
];

export const EXPENSE_CATEGORY_SLUGS = CATEGORIES.filter((c) => c.kind === "expense").map(
  (c) => c.slug,
) as [string, ...string[]];

export function categoryBySlug(slug: string | null | undefined): Category {
  return CATEGORIES.find((c) => c.slug === slug) ?? CATEGORIES.find((c) => c.slug === "other")!;
}
