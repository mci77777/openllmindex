# llmindex — WordPress Integration

Serve your `llmindex.json` manifest from a WordPress site.

## Option 1: Static File (Simplest)

Upload `llmindex.json` to your server:

```
/your-wordpress-root/.well-known/llmindex.json
```

Most hosts allow creating a `.well-known` directory in the web root. If not, use Option 2.

## Option 2: Rewrite Rule + Page

### Step 1: Add rewrite rule

In your theme's `functions.php` or a custom plugin:

```php
<?php
// Serve llmindex.json at /.well-known/llmindex.json
add_action('init', function () {
    add_rewrite_rule(
        '^\.well-known/llmindex\.json$',
        'index.php?llmindex=1',
        'top'
    );
});

add_filter('query_vars', function ($vars) {
    $vars[] = 'llmindex';
    return $vars;
});

add_action('template_redirect', function () {
    if (get_query_var('llmindex')) {
        header('Content-Type: application/json');
        header('Cache-Control: public, max-age=3600');

        echo json_encode([
            'version' => '0.1',
            'updated_at' => gmdate('Y-m-d\TH:i:s\Z'),
            'entity' => [
                'name' => get_bloginfo('name'),
                'canonical_url' => home_url(),
            ],
            'language' => substr(get_locale(), 0, 2),
            'topics' => ['your-industry'],
            'endpoints' => [
                'products' => home_url('/llm/products'),
                'policies' => home_url('/llm/policies'),
                'faq' => home_url('/llm/faq'),
                'about' => home_url('/llm/about'),
            ],
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
        exit;
    }
});
```

### Step 2: Flush rewrite rules

After adding the code, visit **Settings > Permalinks** and click "Save Changes" to flush rewrite rules.

### Step 3: Create /llm/* pages

Create WordPress pages at:
- `/llm/products` — Your product listing
- `/llm/policies` — Shipping, returns, privacy
- `/llm/faq` — Frequently asked questions
- `/llm/about` — Company information

Use a plain text or Markdown-friendly page template for these pages, as LLMs prefer clean text over complex HTML.

## Option 3: WooCommerce Product Feed

If you use WooCommerce, you can auto-generate the JSONL product feed:

```php
<?php
// Add to functions.php or a custom plugin
add_action('init', function () {
    add_rewrite_rule(
        '^llm/feed/products\.jsonl$',
        'index.php?llmindex_feed=products',
        'top'
    );
});

add_filter('query_vars', function ($vars) {
    $vars[] = 'llmindex_feed';
    return $vars;
});

add_action('template_redirect', function () {
    if (get_query_var('llmindex_feed') === 'products') {
        header('Content-Type: application/x-ndjson');
        header('Cache-Control: public, max-age=3600');

        $products = wc_get_products(['limit' => -1, 'status' => 'publish']);

        foreach ($products as $product) {
            $line = [
                'id' => (string) $product->get_id(),
                'title' => $product->get_name(),
                'url' => $product->get_permalink(),
                'image_url' => wp_get_attachment_url($product->get_image_id()),
                'price' => (float) $product->get_price(),
                'currency' => get_woocommerce_currency(),
                'availability' => $product->is_in_stock() ? 'in_stock' : 'out_of_stock',
                'category' => implode(', ', wp_list_pluck(
                    $product->get_category_ids() ? get_terms(['taxonomy' => 'product_cat', 'include' => $product->get_category_ids()]) : [],
                    'name'
                )),
                'updated_at' => $product->get_date_modified()
                    ? $product->get_date_modified()->date('Y-m-d\TH:i:s\Z')
                    : $product->get_date_created()->date('Y-m-d\TH:i:s\Z'),
            ];
            echo json_encode($line, JSON_UNESCAPED_SLASHES) . "\n";
        }
        exit;
    }
});
```

## Verification

Test your setup:

```bash
curl -s https://your-site.com/.well-known/llmindex.json | python -m json.tool
```

Validate with the Python CLI:

```bash
pip install llmindex
llmindex validate your-manifest.json
```
