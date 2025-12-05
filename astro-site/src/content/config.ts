import { defineCollection, z } from "astro:content";

const article = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    date: z.string(),
    cover: z.string().optional(),
    description: z.string().optional(),
    tags: z.array(z.string()).optional(),
    author: z.string().optional(),
  }),
});

export const collections = {
  policy: article,
  news: article,
  industry: article,
  "energy-saving": article,
  reports: article,
};