from decimal import Decimal,InvalidOperation
import re
from app.integrations.channel3.schemas import Channel3Product
from app.procurement.schemas import ProcurementRequirements,ProductScore
from app.procurement.specifications import display_size_violations

WEIGHTS={'specification_match':Decimal('0.35'),'budget_fit':Decimal('0.30'),'availability':Decimal('0.15'),'delivery_suitability':Decimal('0.10'),'listing_completeness':Decimal('0.10')}

def _normal(value: str) -> str:
    return ' '.join(value.casefold().split())

def score_product(product: Channel3Product,requirements: ProcurementRequirements) -> ProductScore:
    attributes={_normal(key):{_normal(entry) for entry in (value if isinstance(value,list) else [value])} for key,value in product.structured_attributes.items()}
    matched=[]
    unmet=[]
    for key,expected in requirements.mandatory_attributes.items():
        if _normal(expected) in attributes.get(_normal(key),set()): matched.append(key)
        else: unmet.append(key)
    display_failures=display_size_violations(requirements.query,product)
    if display_failures: unmet.append('display_size')
    preferred_total=len(requirements.preferred_attributes)
    preferred_matches=sum(1 for key,value in requirements.preferred_attributes.items() if _normal(value) in attributes.get(_normal(key),set()))
    spec_values=[]
    if requirements.mandatory_attributes: spec_values.append(Decimal(100) if not unmet else Decimal(0))
    if preferred_total: spec_values.append(Decimal(preferred_matches*100)/Decimal(preferred_total))
    spec_score=sum(spec_values)/Decimal(len(spec_values)) if spec_values else None
    matching_offers=[offer for offer in product.offers if offer.price.currency==requirements.currency]
    in_stock_offers=[offer for offer in matching_offers if re.sub(r'[\s_-]','',offer.availability.casefold())=='instock']
    prices=[]
    for offer in in_stock_offers:
        try: prices.append(Decimal(str(offer.price.amount)))
        except (InvalidOperation,ValueError): continue
    best_price=min(prices) if prices else None
    budget_score=None
    if requirements.budget is not None and best_price is not None:
        total=best_price*requirements.quantity
        budget_score=Decimal(100) if total<=requirements.budget else max(Decimal(0),requirements.budget/total*Decimal(100))
    availability_values=[re.sub(r'[\s_-]','',offer.availability.casefold()) for offer in matching_offers]
    available=True if 'instock' in availability_values else False if availability_values and all(value=='outofstock' for value in availability_values) else None
    availability_score=Decimal(100) if available is True else Decimal(0) if available is False else None
    completeness_fields=[bool(product.id),bool(product.title),bool(product.description),bool(product.brands),bool(product.images),bool(product.offers)]
    completeness_score=Decimal(sum(completeness_fields)*100)/Decimal(len(completeness_fields))
    observed={'specification_match':spec_score,'budget_fit':budget_score,'availability':availability_score,'delivery_suitability':None,'listing_completeness':completeness_score}
    applicable=[(WEIGHTS[key],value) for key,value in observed.items() if value is not None]
    score=sum(weight*value for weight,value in applicable)/sum(weight for weight,_ in applicable) if applicable else None
    notes=[]
    if requirements.mandatory_attributes and not unmet: notes.append('All mandatory attributes are evidenced in Channel3 structured attributes.')
    if unmet: notes.append('Mandatory attributes are missing or do not match: '+', '.join(unmet)+'.')
    notes.extend(display_failures)
    if best_price is not None: notes.append('Best verified in-stock matching-currency offer: '+str(best_price)+' '+requirements.currency+'.')
    if available is True: notes.append('At least one matching-currency offer is marked in stock.')
    elif available is False: notes.append('Matching-currency offers are marked out of stock.')
    if not matching_offers: notes.append('No offers in the requested currency were returned; price and availability are unknown.')
    elif not in_stock_offers: notes.append('No verified in-stock matching-currency price is available for budget ranking.')
    notes.append('Delivery suitability is unknown because the catalogue response does not establish delivery to the destination.')
    return ProductScore(product_id=product.id,title=product.title,eligible=not unmet,score=score.quantize(Decimal('0.01')) if score is not None else None,matched_attributes=matched,unmet_requirements=unmet,best_unit_price=best_price,currency=requirements.currency if best_price is not None else None,available=available,explanation=notes)

def rank_products(products: list[Channel3Product],requirements: ProcurementRequirements) -> list[ProductScore]:
    scored=[score_product(product,requirements) for product in products]
    return sorted(scored,key=lambda item:(item.eligible,item.score is not None,item.score or Decimal(0)),reverse=True)
