import { defineCollection, z } from "astro:content";

// 定义一个 policy 集合（用于所有政策文章）
const policy = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    date: z.string(),
    description: z.string().optional(),
    category: z.string().optional(),
    tags: z.array(z.string()).optional(),
  }),
});

export const collections = { policy };