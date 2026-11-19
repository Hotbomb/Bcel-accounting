import type { Extraction } from "@/lib/receipt/schema";

// Made-up data shaped like the three real BCEL One receipt types.
export const transferToPerson: Extraction = {
  is_bcel_receipt: true,
  receipt_type: "transfer",
  success: true,
  date_time: "2026-11-18T20:40:19",
  amount: 290000,
  currency: "LAK",
  to_amount: null,
  to_currency: null,
  exchange_rate: null,
  fee: null,
  from_name: "SOMSAK TESTUSER MR",
  from_account_masked: "222-12-xxxxx254",
  recipient_name: "BOUNMY EXAMPLE MR",
  recipient_account_masked: "030-12-00-xxxxx040-001",
  transaction_ref: "202611187019761",
  ticket_ref: "BFD5K25BDHJL",
  memo: ".",
  suggested_category: "people",
  confidence: 0.95,
};

export const ownExchange: Extraction = {
  ...transferToPerson,
  receipt_type: "currency_exchange",
  date_time: "2026-11-16T12:48:02",
  amount: 500,
  currency: "THB",
  to_amount: 333340,
  to_currency: "LAK",
  exchange_rate: 666.68,
  from_account_masked: "222-12-xxxxx815",
  recipient_name: "SOMSAK TESTUSER MR",
  recipient_account_masked: "222-12-xxxxx254",
  transaction_ref: "202611163723423",
  ticket_ref: "BEEHOG55KKI9",
  suggested_category: "other",
};

export const qrPayment: Extraction = {
  ...transferToPerson,
  receipt_type: "qr_payment",
  date_time: "2026-11-12T15:00:05",
  amount: 30000,
  from_name: null,
  recipient_name: "ຮ້ານທົດສອບ (ຮ້ານກາເຟ)",
  recipient_account_masked: null,
  transaction_ref: "202 6111 2443 6407",
  ticket_ref: "BEWE8CUAFKU4",
  memo: null,
  suggested_category: "food",
};

export const notReceipt: Extraction = {
  ...transferToPerson,
  is_bcel_receipt: false,
  receipt_type: "other",
  success: false,
  date_time: null,
  amount: null,
  transaction_ref: null,
  suggested_category: "other",
  confidence: 0.99,
};
