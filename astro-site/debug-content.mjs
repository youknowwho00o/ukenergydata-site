import { getEntryBySlug } from "astro:content";

const slug = "2025-11-18-auto-policy";

const post = await getEntryBySlug("policy", slug);

console.log("ENTRY RAW:", post);
console.log("FRONTMATTER:", post?.data);
