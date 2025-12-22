# Webshop Auto Publish - DBW Base Integration Guide

**Module**: webshop_auto_publish (suite)
**Version**: 19.0.1.0.0
**Status**: ✅ Production Ready
**Integration Target**: DBW Odoo Base
**Date**: December 2025

---

## Table of Contents

1. [Module Analysis](#1-module-analysis)
2. [DBW Base Integration Opportunities](#2-dbw-base-integration-opportunities)
3. [Hybrid Implementation Pattern](#3-hybrid-implementation-pattern)
4. [API Contract](#4-api-contract)
5. [Migration Checklist](#5-migration-checklist)
6. [Testing Scenarios](#6-testing-scenarios)

---

## 1. Module Analysis

### 1.1 Overview

**Webshop Auto Publish Suite** bestaat uit 4 gerelateerde modules die samen de product lifecycle management voor een webshop verzorgen:

#### Core Modules

**A. webshop_quality_rules** (Paid - €49/month)
- **Purpose**: Configureerbare validatie regels per website categorie
- **Key Features**:
  - Product validation against quality standards
  - Computed field `is_ready_for_publication`
  - Auto-publish/depublish based on validation
  - Supplier lifecycle management (archive products without current suppliers)
- **Critical Data**: 
  - `product.template.is_ready_for_publication` (Boolean, stored)
  - `product.template.validation_errors` (Text, stored)
  - `product.supplierinfo.is_current_supplier` (Boolean, computed)

**B. webshop_catalog_dashboard** (Free - Marketing Tool)
- **Purpose**: Visueel dashboard voor product status
- **Key Features**:
  - Tile-based overview (klaar, missing image, missing price, etc.)
  - One-click access to filtered product lists
- **Critical Data**: Dashboard tiles gebruik search_count queries

**C. webshop_product_creator** (Currently removed, can be restored)
- **Purpose**: Bulk product creation from supplier import errors
- **Key Features**:
  - Quick create single products
  - Bulk create with preview
  - Batch processing for large volumes
- **Status**: Module removed from production, code in git history

**D. webshop_auto_publish** (Main module - legacy)
- **Status**: Legacy module, functionality absorbed by quality_rules

### 1.2 Data Flow

```
Supplier Import (product_supplier_sync)
  ↓
Product Created/Updated
  ↓
Quality Rules Validation (cron every 15min)
  ↓ 
is_ready_for_publication computed
  ↓
Auto Publish/Depublish (if enforce_strictly=True)
  ↓
Dashboard Shows Status
```

### 1.3 Key Models & Methods

#### product.template (Extended)

**Fields Added**:
```python
# webshop_quality_rules/models/product_template.py
need_validation = fields.Boolean(default=True)
is_ready_for_publication = fields.Boolean(compute='_compute_is_ready', store=True)
enforce_strictly = fields.Boolean(default=True, string="Streng afdwingen")
validation_errors = fields.Text(compute='_compute_is_ready', store=True)
```

**Methods**:
```python
@api.depends('image_1920', 'list_price', 'description_ecommerce', 'description', 
             'barcode', 'public_categ_ids', 'seller_ids', 'seller_ids.is_current_supplier')
def _compute_is_ready(self):
    # Validates against category rules
    # Returns is_ready_for_publication + validation_errors

@api.model
def cron_validate_products(self):
    # Runs every 15 minutes
    # Validates products with need_validation=True
    # Auto-publishes ready products
    # Auto-depublishes invalid products (if enforce_strictly)

@api.model
def cron_archive_products_without_suppliers(self):
    # Runs every hour
    # Archives products without current suppliers and no own stock
    # Batch processing (500 products per batch)
```

#### product.supplierinfo (Extended)

**Fields Added**:
```python
# REMOVED - No longer needed
# supplier_sync module now uses standard 'active' field on product.supplierinfo
# Active suppliers are those in the latest import (non-archived)
```

**Logic**:
- Uses standard `active` field on `product.supplierinfo`
- Supplier sync module sets `active=False` when archiving old import data
- Product validation only checks suppliers with `active=True`
- Simpler and more reliable than date-based comparison

#### product.public.category (Extended)

**Fields Added** (Category-specific rules):
```python
# webshop_quality_rules/models/product_public_category.py
auto_publish = fields.Boolean(default=False)
min_supplier_stock = fields.Integer(default=5)
require_ean = fields.Boolean(default=False)
require_brand = fields.Boolean(default=False)
require_short_description = fields.Boolean(default=False)
require_long_description = fields.Boolean(default=False)
price_drop_threshold = fields.Float(default=15.0)
```

### 1.4 Validation Rules

**Standaard Checks** (in `_compute_is_ready`):
1. ❌ Mist hoofdafbeelding (image_1920)
2. ❌ Verkoopprijs ≤ 0 (list_price)
3. ❌ Mist e-commerce beschrijving (description_ecommerce) - if category requires
4. ❌ Mist uitgebreide omschrijving (description) - if category requires
5. ❌ Mist EAN/barcode - if category requires
6. ❌ Mist merk (brand_id) - if category requires
7. ❌ Geen actuele leverancier met ≥X stuks (is_current_supplier + supplier_stock)
8. ⚠️ Prijsdaling >15% - placeholder for future implementation

**Category-Level Configuration**:
- Each website category can have different requirements
- Strictest rule wins if product in multiple categories
- `auto_publish` enables automatic publication for that category

### 1.5 Scheduled Actions

**Cron Job 1**: Product Validation
- **ID**: `cron_validate_products`
- **Interval**: 15 minutes
- **Batch Size**: N/A (processes all dirty products)
- **Function**: `model.cron_validate_products()`

**Cron Job 2**: Archive Without Suppliers
- **ID**: `cron_archive_no_suppliers`
- **Interval**: 1 hour
- **Batch Size**: 500 products
- **Function**: `model.cron_archive_products_without_suppliers()`

### 1.6 Dependencies

**Current**:
- `website_sale` - Website integration
- `purchase` - Supplier info
- `product` - Core product model

**Missing** (should have):
- `product_supplier_sync` - For supplier lifecycle tracking
- `stock` - For own stock checks (qty_available)

---

## 2. DBW Base Integration Opportunities

### 2.1 What Can Webshop Use from DBW Base?

#### A. **product_validation_service** ⭐ PRIMARY TARGET

**Current Problem**:
Module has complex `_compute_is_ready()` logic (130+ lines) that duplicates validation logic.

**DBW Solution**:
```python
# FROM DBW Base: services/product_validation_service.py
def validate_product(self, product, category_rules=None):
    """
    Central validation service
    Returns: {
        'is_valid': bool,
        'errors': [str],
        'warnings': [str],
        'score': int (0-100)
    }
    """
```

**Benefits**:
- ✅ Single source of truth for validation
- ✅ Consistent validation across all modules
- ✅ Easy to extend validation rules
- ✅ Standardized error messages

#### B. **product_lifecycle_service**

**Current Problem**:
Archive logic in cron job, no central lifecycle management.

**DBW Solution**:
```python
# FROM DBW Base: services/product_lifecycle_service.py
def should_archive_product(self, product):
    # Checks: no suppliers, no stock, inactive categories
    
def archive_products_batch(self, products, reason=None):
    # Bulk archive with logging
```

**Benefits**:
- ✅ Centralized archive logic
- ✅ Audit trail (why archived)
- ✅ Easier to reactivate products

#### C. **product_categorization_helper**

**Current Use**:
Dashboard filters by category, manual domain building.

**DBW Solution**:
```python
# FROM DBW Base: helpers/product_categorization_helper.py
def get_products_by_validation_status(self, status='ready'):
    # Returns domain + context
    
def get_category_rules_for_product(self, product):
    # Returns strictest rules from all categories
```

#### D. **batch_processor**

**Current Use**:
Custom batch logic in `cron_archive_products_without_suppliers`.

**DBW Solution**:
```python
# FROM DBW Base: tools/batch_processor.py
def process_in_batches(self, recordset, batch_size=500, callback=None):
    # Handles pagination, commits, logging
```

### 2.2 What Can Webshop Provide to DBW Base?

#### A. **Validation Rules Configuration UI** ✅ UNIQUE VALUE

**Current Asset**:
- Category-level validation config (product_public_category_views.xml)
- Per-category thresholds (min_supplier_stock, price_drop_threshold)
- Boolean toggles (require_ean, auto_publish, etc.)

**DBW Integration**:
```python
# CONTRIBUTE TO: dbw_base/models/product_category_rules.py
class ProductCategoryRules(models.Model):
    _name = 'product.category.rules'
    
    # Webshop module provides UI + defaults
    # DBW Base provides service layer
```

#### B. **Supplier Currency Detection** ✅ PROVEN LOGIC

**Current Asset**:
From `is_current_supplier` logic - detecting outdated supplier data.

**DBW Integration**:
```python
# CONTRIBUTE TO: dbw_base/helpers/supplier_helper.py
def is_supplier_data_current(self, supplierinfo):
    # Logic from webshop_quality_rules/models/product_supplierinfo.py
```

#### C. **Batch Archive Patterns** ✅ PERFORMANCE

**Current Asset**:
Optimized batch processing with commits, bulk writes.

**DBW Integration**:
Pattern can be extracted to `batch_processor` tool in DBW Base.

---

## 3. Hybrid Implementation Pattern

### 3.1 Phase 1: Detection Layer

Add detection logic to check if DBW Base is available:

```python
# webshop_quality_rules/models/product_template.py

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def _has_dbw_base(self):
        """Check if DBW Base validation service is available"""
        return (
            hasattr(self.env, 'get_service') and 
            self.env.get_service('product_validation_service') is not None
        )
    
    @api.depends('image_1920', 'list_price', 'description_ecommerce', 'description', 
                 'barcode', 'public_categ_ids', 'seller_ids', 'seller_ids.is_current_supplier')
    def _compute_is_ready(self):
        """
        Hybrid validation: Use DBW Base if available, fallback to local logic
        """
        if self._has_dbw_base():
            self._compute_is_ready_dbw()
        else:
            self._compute_is_ready_local()
    
    def _compute_is_ready_dbw(self):
        """Validation using DBW Base service"""
        validation_service = self.env.get_service('product_validation_service')
        
        for product in self:
            # Get category rules
            category_rules = self._get_category_rules(product)
            
            # Call DBW validation service
            result = validation_service.validate_product(
                product, 
                category_rules=category_rules
            )
            
            product.is_ready_for_publication = result['is_valid']
            product.validation_errors = '\n'.join(result['errors']) if result['errors'] else '✅ Alle controles geslaagd'
    
    def _compute_is_ready_local(self):
        """
        Fallback validation (current logic)
        KEEP THIS FOR BACKWARD COMPATIBILITY
        """
        # ... existing 130 lines of validation logic ...
        # This is the EXACT current code, untouched
    
    def _get_category_rules(self, product):
        """Extract category rules for validation"""
        categories = product.public_categ_ids
        
        if not categories:
            return None
        
        # Get strictest rules
        return {
            'min_supplier_stock': max([cat.min_supplier_stock or 5 for cat in categories]),
            'require_ean': any(cat.require_ean for cat in categories),
            'require_brand': any(cat.require_brand for cat in categories),
            'require_short_description': any(cat.require_short_description for cat in categories),
            'require_long_description': any(cat.require_long_description for cat in categories),
            'price_drop_threshold': min([cat.price_drop_threshold or 15.0 for cat in categories]),
            'auto_publish': any(cat.auto_publish for cat in categories),
        }
```

### 3.2 Phase 2: Archive Service Integration

```python
# webshop_quality_rules/models/product_template.py

@api.model
def cron_archive_products_without_suppliers(self):
    """
    Hybrid archive: Use DBW service if available, fallback to local
    """
    if self._has_dbw_base():
        return self._archive_with_dbw_service()
    else:
        return self._archive_local()

def _archive_with_dbw_service(self):
    """Archive using DBW Base lifecycle service"""
    lifecycle_service = self.env.get_service('product_lifecycle_service')
    batch_processor = self.env.get_tool('batch_processor')
    
    _logger.info("Using DBW Base for product archiving")
    
    # Get all active products
    products = self.search([('active', '=', True)])
    
    # Filter products that should be archived
    products_to_archive = products.filtered(
        lambda p: lifecycle_service.should_archive_product(
            p, 
            reason='no_current_suppliers'
        )
    )
    
    # Batch process with DBW tool
    def archive_callback(batch):
        lifecycle_service.archive_products_batch(
            batch, 
            reason='No current suppliers and no own stock'
        )
    
    batch_processor.process_in_batches(
        products_to_archive,
        batch_size=500,
        callback=archive_callback
    )
    
    return True

def _archive_local(self):
    """
    Fallback archive logic (current implementation)
    KEEP THIS FOR BACKWARD COMPATIBILITY
    """
    # ... existing batch processing code ...
    # This is the EXACT current code, untouched
```

### 3.3 Phase 3: Dashboard Integration

```python
# webshop_catalog_dashboard/models/dashboard.py

class CatalogDashboard(models.Model):
    _name = 'catalog.dashboard'
    
    def _has_dbw_base(self):
        """Check if DBW Base helpers are available"""
        return (
            hasattr(self.env, 'get_helper') and 
            self.env.get_helper('product_categorization_helper') is not None
        )
    
    @api.depends_context('uid')
    def _compute_ready_count(self):
        """Hybrid count: Use DBW helper if available"""
        for rec in self:
            if rec._has_dbw_base():
                rec._compute_ready_count_dbw()
            else:
                rec._compute_ready_count_local()
    
    def _compute_ready_count_dbw(self):
        """Count using DBW Base helper"""
        helper = self.env.get_helper('product_categorization_helper')
        domain = helper.get_products_by_validation_status('ready')
        self.ready_count = self.env['product.template'].search_count(domain)
    
    def _compute_ready_count_local(self):
        """Fallback count (current implementation)"""
        # ... existing search_count logic ...
```

---

## 4. API Contract

### 4.1 Services Required from DBW Base

#### A. product_validation_service

**Location**: `dbw_base/services/product_validation_service.py`

**Interface**:
```python
class ProductValidationService:
    
    def validate_product(self, product, category_rules=None):
        """
        Validate a single product against quality rules
        
        Args:
            product (product.template): Product to validate
            category_rules (dict, optional): Override category rules
                {
                    'min_supplier_stock': int,
                    'require_ean': bool,
                    'require_brand': bool,
                    'require_short_description': bool,
                    'require_long_description': bool,
                    'price_drop_threshold': float,
                }
        
        Returns:
            dict: {
                'is_valid': bool,          # Overall pass/fail
                'errors': [str],           # Blocking issues
                'warnings': [str],         # Non-blocking issues
                'score': int (0-100),      # Quality score
                'checks': {                # Individual check results
                    'has_image': bool,
                    'has_price': bool,
                    'has_description': bool,
                    'has_ean': bool,
                    'has_brand': bool,
                    'has_supplier': bool,
                    'price_valid': bool,
                }
            }
        
        Guarantees:
            - Never raises exceptions (catches all, returns errors in dict)
            - Always returns dict with all keys present
            - errors list uses standard format: "❌ {message}"
            - warnings list uses format: "⚠️ {message}"
        """
```

#### B. product_lifecycle_service

**Location**: `dbw_base/services/product_lifecycle_service.py`

**Interface**:
```python
class ProductLifecycleService:
    
    def should_archive_product(self, product, reason=None):
        """
        Determine if product should be archived
        
        Args:
            product (product.template): Product to check
            reason (str, optional): Specific reason to check
                Options: 'no_suppliers', 'no_stock', 'inactive', 'all'
        
        Returns:
            bool: True if product should be archived
            
        Checks:
            - No current suppliers with stock
            - No own stock (qty_available <= 0)
            - All categories inactive
            - Manual archive flag
        """
    
    def archive_products_batch(self, products, reason=None, dry_run=False):
        """
        Archive multiple products with audit logging
        
        Args:
            products (product.template recordset): Products to archive
            reason (str, optional): Reason for archiving
            dry_run (bool): If True, don't actually archive (just log)
        
        Returns:
            dict: {
                'archived': int,        # Number archived
                'skipped': int,         # Number skipped
                'ids': [int],          # IDs of archived products
                'errors': [str],       # Any errors encountered
            }
        
        Side Effects:
            - Sets active=False
            - Sets website_published=False
            - Creates audit log entry
            - Triggers archive webhook (if configured)
        """
```

#### C. batch_processor (Tool)

**Location**: `dbw_base/tools/batch_processor.py`

**Interface**:
```python
class BatchProcessor:
    
    def process_in_batches(self, recordset, batch_size=500, callback=None):
        """
        Process recordset in batches with commits
        
        Args:
            recordset (odoo.models): Any Odoo recordset
            batch_size (int): Records per batch
            callback (callable): Function to call per batch
                Signature: callback(batch_recordset) -> None
        
        Returns:
            dict: {
                'total': int,           # Total records processed
                'batches': int,         # Number of batches
                'duration': float,      # Seconds elapsed
                'errors': [str],        # Any errors
            }
        
        Guarantees:
            - Commits after each batch
            - Catches exceptions per batch (continues on error)
            - Logs progress every batch
            - Returns statistics
        """
```

#### D. product_categorization_helper

**Location**: `dbw_base/helpers/product_categorization_helper.py`

**Interface**:
```python
class ProductCategorizationHelper:
    
    def get_products_by_validation_status(self, status='ready'):
        """
        Get domain for products by validation status
        
        Args:
            status (str): Status filter
                Options: 'ready', 'missing_image', 'missing_price', 
                        'missing_description', 'missing_ean', 'all_invalid'
        
        Returns:
            list: Odoo domain filter
            
        Example:
            domain = helper.get_products_by_validation_status('ready')
            products = env['product.template'].search(domain)
        """
    
    def get_category_rules_for_product(self, product):
        """
        Get consolidated validation rules for a product
        
        Args:
            product (product.template): Product to check
        
        Returns:
            dict: Consolidated rules (strictest wins)
            None: If product has no categories
        """
```

### 4.2 Data Contracts

#### Validation Result Format

```python
{
    'is_valid': False,
    'errors': [
        '❌ Mist hoofdafbeelding',
        '❌ Geen actuele leverancier met ≥5 stuks'
    ],
    'warnings': [
        '⚠️ Prijsdaling >15% - controle nodig'
    ],
    'score': 65,  # 0-100 quality score
    'checks': {
        'has_image': False,
        'has_price': True,
        'has_description': True,
        'has_ean': True,
        'has_brand': False,
        'has_supplier': False,
        'price_valid': True,
    }
}
```

#### Category Rules Format

```python
{
    'min_supplier_stock': 5,              # Integer, default 5
    'require_ean': False,                 # Boolean
    'require_brand': False,               # Boolean
    'require_short_description': True,    # Boolean
    'require_long_description': False,    # Boolean
    'price_drop_threshold': 15.0,         # Float, percentage
    'auto_publish': True,                 # Boolean
}
```

---

## 5. Migration Checklist

### Phase 1: Preparation (Testing in Docker)

#### Step 1: Install DBW Base (Dev Environment)

```bash
# On odoo19-dev-web-1 container
cd /mnt/extra-addons/
git clone https://github.com/sybdeb/dbw-odoo-base.git dbw_base
chown -R odoo:odoo dbw_base

# Restart Odoo
docker restart odoo19-dev-web-1

# Install via UI or CLI
docker exec odoo19-dev-web-1 odoo -d nerbys_dev -i dbw_base --stop-after-init
```

#### Step 2: Verify DBW Base Services

```python
# In Odoo shell (docker exec odoo19-dev-web-1 odoo shell -d nerbys_dev)
validation_service = env.get_service('product_validation_service')
print(validation_service)  # Should not be None

lifecycle_service = env.get_service('product_lifecycle_service')
print(lifecycle_service)  # Should not be None

batch_processor = env.get_tool('batch_processor')
print(batch_processor)  # Should not be None
```

#### Step 3: Test Hybrid Detection

```python
# Test detection method
product = env['product.template'].search([], limit=1)
has_dbw = product._has_dbw_base()
print(f"DBW Base available: {has_dbw}")  # Should be True
```

### Phase 2: Hybrid Implementation

#### Step 1: Update webshop_quality_rules

```bash
# Update module code (add hybrid methods)
cd /mnt/extra-addons/webshop_quality_rules/models/
# Edit product_template.py with hybrid code from Section 3.1
```

#### Step 2: Update Module Version

```python
# webshop_quality_rules/__manifest__.py
{
    'version': '19.0.2.0.0',  # Bump to 2.0.0
    'depends': ['website_sale', 'purchase', 'product'],
    # Note: dbw_base is NOT a hard dependency (hybrid mode)
}
```

#### Step 3: Upgrade Module (Dev)

```bash
docker exec odoo19-dev-web-1 odoo -d nerbys_dev -u webshop_quality_rules --stop-after-init
docker restart odoo19-dev-web-1
```

#### Step 4: Test Validation (Dev)

```python
# In Odoo dev instance
product = env['product.template'].search([('name', '=', 'Test Product')])
product._compute_is_ready()

# Check logs - should see "Using DBW Base for validation"
print(product.is_ready_for_publication)
print(product.validation_errors)
```

#### Step 5: Test Archive Cron (Dev)

```bash
# Manually trigger cron
docker exec odoo19-dev-db-1 psql -U odoo -d nerbys_dev -c \
  "UPDATE ir_cron SET nextcall = NOW() WHERE id = (SELECT id FROM ir_cron WHERE cron_name LIKE '%Archive%');"

# Check logs
docker logs -f odoo19-dev-web-1 | grep -E "(Archive|DBW)"
```

### Phase 3: Production Deployment

#### Step 1: Git Commit & Push

```bash
cd /c/Users/Sybde/Projects/webshop_auto_publish
git add -A
git commit -m "feat: Hybrid DBW Base integration for webshop_quality_rules

- Add _has_dbw_base() detection method
- Add _compute_is_ready_dbw() using validation service
- Add _archive_with_dbw_service() using lifecycle service
- Keep local fallback methods for backward compatibility
- No breaking changes, fully backward compatible"
git push
```

#### Step 2: Deploy to Production

```bash
# Deploy webshop_quality_rules
cd /c/Users/Sybde/Projects/webshop_auto_publish
tar -czf webshop_quality_rules.tar.gz webshop_quality_rules/
scp webshop_quality_rules.tar.gz hetzner-sybren:/tmp/

ssh hetzner-sybren "
  docker cp /tmp/webshop_quality_rules.tar.gz odoo19-prod-web-1:/tmp/ &&
  docker exec -u root odoo19-prod-web-1 bash -c '
    cd /tmp &&
    tar -xzf webshop_quality_rules.tar.gz &&
    rm -rf /mnt/extra-addons/webshop_quality_rules &&
    mv webshop_quality_rules /mnt/extra-addons/ &&
    chown -R odoo:odoo /mnt/extra-addons/webshop_quality_rules &&
    rm /tmp/webshop_quality_rules.tar.gz
  ' &&
  docker restart odoo19-prod-web-1 &&
  echo '✓ Hybrid webshop_quality_rules deployed'
"
```

#### Step 3: Verify Production (Without DBW Base)

```bash
# Should work WITHOUT dbw_base (fallback mode)
ssh hetzner-sybren "docker exec odoo19-prod-web-1 python3 << 'PYEOF'
import odoo
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf'])
with odoo.api.Environment.manage():
    registry = odoo.registry('nerbys')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, 1, {})
        product = env['product.template'].search([], limit=1)
        has_dbw = product._has_dbw_base()
        print(f'DBW Base available: {has_dbw}')  # Should be False
        product._compute_is_ready()
        print(f'Validation works: {product.is_ready_for_publication is not None}')
PYEOF
"
```

#### Step 4: Optional - Install DBW Base (Production)

```bash
# ONLY if you want to use DBW services in production
ssh hetzner-sybren "
  cd /mnt/extra-addons/ &&
  git clone https://github.com/sybdeb/dbw-odoo-base.git dbw_base &&
  chown -R odoo:odoo dbw_base &&
  docker restart odoo19-prod-web-1
"

# Install via UI: Apps → Search "DBW Base" → Install
```

### Phase 4: Monitoring

#### Key Metrics to Track

```sql
-- Check validation service usage
SELECT COUNT(*) 
FROM ir_logging 
WHERE name LIKE '%DBW%validation%'
AND create_date > NOW() - INTERVAL '1 day';

-- Check archive service usage
SELECT COUNT(*) 
FROM ir_logging 
WHERE name LIKE '%DBW%archive%'
AND create_date > NOW() - INTERVAL '1 day';

-- Products validated today
SELECT COUNT(*) 
FROM product_template 
WHERE write_date > CURRENT_DATE 
AND is_ready_for_publication IS NOT NULL;
```

#### Rollback Plan

```bash
# If issues occur, revert to previous version
git checkout HEAD~1 webshop_quality_rules/
tar -czf webshop_quality_rules.tar.gz webshop_quality_rules/
# ... deploy previous version ...
```

---

## 6. Testing Scenarios

### 6.1 Unit Tests (Hybrid Mode)

#### Test 1: Detection Works

```python
def test_dbw_detection(self):
    """Test _has_dbw_base() returns correct boolean"""
    product = self.env['product.template'].create({
        'name': 'Test Product',
        'type': 'consu',
    })
    
    # Should not crash regardless of DBW availability
    has_dbw = product._has_dbw_base()
    self.assertIsInstance(has_dbw, bool)
```

#### Test 2: Fallback Works Without DBW

```python
def test_validation_without_dbw(self):
    """Test validation works without DBW Base"""
    # Ensure DBW Base is not installed
    self.assertFalse(hasattr(self.env, 'get_service'))
    
    product = self.env['product.template'].create({
        'name': 'Test Product',
        'list_price': 100.0,
        'image_1920': b'fake_image_data',
    })
    
    product._compute_is_ready()
    
    # Should have result (even without DBW)
    self.assertIsNotNone(product.is_ready_for_publication)
    self.assertIsNotNone(product.validation_errors)
```

#### Test 3: DBW Service Called When Available

```python
def test_validation_with_dbw(self):
    """Test validation uses DBW service when available"""
    # Mock DBW service
    mock_service = MagicMock()
    mock_service.validate_product.return_value = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'score': 100,
    }
    
    with patch.object(self.env, 'get_service', return_value=mock_service):
        product = self.env['product.template'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })
        
        product._compute_is_ready()
        
        # Verify service was called
        mock_service.validate_product.assert_called_once()
        self.assertTrue(product.is_ready_for_publication)
```

### 6.2 Integration Tests

#### Test 4: End-to-End Validation

```python
def test_e2e_product_validation(self):
    """Test complete validation flow"""
    # Create category with rules
    category = self.env['product.public.category'].create({
        'name': 'Test Category',
        'auto_publish': True,
        'min_supplier_stock': 5,
        'require_ean': True,
    })
    
    # Create product (initially invalid)
    product = self.env['product.template'].create({
        'name': 'Test Product',
        'list_price': 0,  # Invalid!
        'public_categ_ids': [(6, 0, [category.id])],
    })
    
    product._compute_is_ready()
    self.assertFalse(product.is_ready_for_publication)
    self.assertIn('❌', product.validation_errors)
    
    # Fix product
    product.list_price = 100.0
    product.image_1920 = b'fake_image'
    product.barcode = '1234567890123'
    
    product._compute_is_ready()
    # Should pass now (if has supplier with stock)
```

#### Test 5: Archive Cron Job

```python
def test_archive_cron_execution(self):
    """Test archive cron runs without errors"""
    # Create product without suppliers
    product = self.env['product.template'].create({
        'name': 'Orphan Product',
        'active': True,
    })
    
    # Run cron
    self.env['product.template'].cron_archive_products_without_suppliers()
    
    # Product should be archived
    product.invalidate_cache()
    self.assertFalse(product.active)
```

### 6.3 Performance Tests

#### Test 6: Batch Processing Performance

```python
def test_batch_performance(self):
    """Test archive cron handles 10k products efficiently"""
    import time
    
    # Create 10,000 test products
    products = self.env['product.template'].create([
        {'name': f'Product {i}', 'active': True}
        for i in range(10000)
    ])
    
    start = time.time()
    self.env['product.template'].cron_archive_products_without_suppliers()
    duration = time.time() - start
    
    # Should complete in under 60 seconds
    self.assertLess(duration, 60.0)
    
    # Check commit rate (should have committed multiple times)
    # (Check via transaction log or database)
```

### 6.4 User Acceptance Tests

#### UAT 1: Dashboard Shows Correct Counts

**Steps**:
1. Navigate to Webshop → Dashboard
2. Check "Klaar voor publicatie" count
3. Click tile → should show filtered products
4. Verify no archived products in list

**Expected**:
- Count matches search result
- Only active products shown
- Quality rules correctly applied

#### UAT 2: Product Validation Updates Automatically

**Steps**:
1. Create product with missing image
2. Wait 15 minutes (or trigger cron manually)
3. Check "Webshop Validatie" tab
4. See "❌ Mist hoofdafbeelding" error
5. Upload image, save product
6. Wait 15 minutes
7. Error should disappear

**Expected**:
- Validation errors appear/disappear correctly
- Published state updates automatically (if enforce_strictly)

#### UAT 3: Archive Workflow

**Steps**:
1. Create product with supplier (12 stock)
2. Product should be validated as ready
3. Run new supplier import WITHOUT this product
4. Wait 1 hour (archive cron runs)
5. Product should be archived

**Expected**:
- `active = False`
- `website_published = False`
- `is_current_supplier = False` on old supplier record

---

## 7. Troubleshooting

### Common Issues

#### Issue 1: "DBW Base not detected but installed"

**Symptom**: `_has_dbw_base()` returns False even after installing dbw_base

**Solution**:
```bash
# Restart Odoo to reload registry
docker restart odoo19-prod-web-1

# Verify installation
docker exec odoo19-prod-db-1 psql -U odoo -d nerbys -c \
  "SELECT state FROM ir_module_module WHERE name = 'dbw_base';"
# Should return 'installed'
```

#### Issue 2: "Validation slower with DBW Base"

**Symptom**: Cron jobs take longer after DBW integration

**Diagnosis**:
```python
# Check if service calls are cached
import logging
_logger = logging.getLogger(__name__)

def _compute_is_ready_dbw(self):
    start = time.time()
    result = validation_service.validate_product(self)
    _logger.info(f"Validation took {time.time() - start:.2f}s")
```

**Solution**: Enable caching in DBW Base service layer

#### Issue 3: "Products not archiving"

**Symptom**: Archive cron runs but no products archived

**Diagnosis**:
```sql
-- Check is_current_supplier values
SELECT COUNT(*), is_current_supplier 
FROM product_supplierinfo 
GROUP BY is_current_supplier;

-- Check products with suppliers
SELECT pt.id, pt.name, COUNT(ps.id) as supplier_count
FROM product_template pt
LEFT JOIN product_supplierinfo ps ON pt.id = ps.product_tmpl_id
WHERE pt.active = true
GROUP BY pt.id
HAVING COUNT(ps.id) > 0
LIMIT 10;
```

**Solution**: Verify `is_current_supplier` compute logic, check supplier sync dates

---

## 8. API Extension Points

### 8.1 Custom Validation Rules

**Pattern**: Allow custom modules to add validation checks

```python
# In custom module
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def _get_custom_validation_checks(self):
        """
        Override to add custom validation rules
        
        Returns:
            dict: {
                'check_name': {
                    'passed': bool,
                    'error': str (if failed),
                    'warning': str (if warning),
                }
            }
        """
        checks = super()._get_custom_validation_checks()
        
        # Add custom check
        checks['custom_field_present'] = {
            'passed': bool(self.custom_field),
            'error': '❌ Custom field missing' if not self.custom_field else None,
        }
        
        return checks
```

### 8.2 Custom Archive Conditions

**Pattern**: Allow custom modules to prevent archiving

```python
# In custom module
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def _should_prevent_archive(self):
        """
        Override to prevent archiving based on custom logic
        
        Returns:
            tuple: (should_prevent: bool, reason: str)
        """
        prevent, reason = super()._should_prevent_archive()
        
        if prevent:
            return prevent, reason
        
        # Custom logic
        if self.custom_flag:
            return True, "Custom flag set - manual review required"
        
        return False, None
```

---

## 9. Conclusion

### Summary

**Webshop Auto Publish Suite** is ready for DBW Base integration with:

✅ **No breaking changes** - Hybrid mode maintains backward compatibility
✅ **Clear API contract** - Well-defined service interfaces
✅ **Proven patterns** - Batch processing, validation logic tested in production
✅ **Migration path** - Step-by-step deployment guide

### Next Steps

1. **Immediate**: Deploy hybrid implementation to dev
2. **Short-term**: Test with DBW Base in dev environment
3. **Mid-term**: Production deployment (hybrid mode first)
4. **Long-term**: Contribute validation UI patterns to DBW Base

### Contact

**Module Maintainer**: Sybren De Boever
**GitHub**: https://github.com/sybdeb/webshop-auto-publish
**DBW Base**: https://github.com/sybdeb/dbw-odoo-base

---

*Last Updated: December 19, 2025*
*Document Version: 1.0.0*
