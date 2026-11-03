from decimal import Decimal, InvalidOperation
from app.integrations.channel3.schemas import Channel3Product
from app.procurement.schemas import ProcurementRequirements, ProductScore

WEIGHTS={'specification_match':Decimal('0.35'),'budget_fit':Decimal('0.30'),'availability':Decimal('0.15'),'delivery_suitability':Decimal('0.10'),'listing_completeness':Decimal('0.10')}

def _normal(value: str) -> str:
    return ' '.join(value.casefold().split())

def score_product(product: Channel3Product, requirements: ProcurementRequirements) -> ProductScore:
    attributes={_normal(key):_normal(value) for key,value in product.structured_attributes.items()}
    matched=[]; unmet=[]
    for key,expected in requirements.mandatory_attributes.items():
        actual=attributes.get(_normal(key))
        if actual==_normal(expected): matched.append(key)
        else: unmet.append(key)
    preferred_total=len(requirements.preferred_attributes)
    preferred_matches=sum(1 for key,value in requirements.preferred_attributes.items() if attributes.get(_normal(key))==_normal(value))
    spec_values=[]
    if requirements.mandatory_attributes:
        spec_values.append(Decimal(100) if not unmet else Decimal(0))
    if preferred_total:
        spec_values.append(Decimal(preferred_matches*100/preferred_total))
    spec_score=sum(spec_values)/len(spec_values) if spec_values else None

    matching_offers=[offer for offer in product.offers if offer.currency==requirements.currency]
    prices=[]
    for offer in matching_offers:
        try: prices.append(Decimal(str(offer.price)))
        except (InvalidOperation,ValueError): continue
    best_price=min(prices) if prices else None
    budget_score=None
    if requirements.budget is not None and best_price is not None:
        total=best_price*requirements.quantity
        budget_score=Decimal(100) if total<=requirements.budget else max(Decimal(0),requirements.budget/total*100)

    availability_values=[offer.availability.casefold() for offer in matching_offers]
    available=True if 'instock' in availability_values else False if availability_values and all(v=='outofstock' for v in availability_values) else None
    availability_score=Decimal(100) if available is True else Decimal(0) if available is False else None

    completeness_fields=[bool(product.id),bool(product.title),bool(product.description),bool(product.brands),bool(product.images),bool(product.offers)]
    completeness_score=Decimal(sum(completeness_fields)*100/len(completeness_fields))
    observed={'specification_match':spec_score,'budget_fit':budget_score,'availability':availability_score,'delivery_suitability':None,'listing_completeness':completeness_score}
    applicable=[(WEIGHTS[key],value) for key,value in observed.items() if value is not None]
    score=sum(weight*value for weight,value in applicable)/sum(weight for weight,_ in applicable) if applicable else None
    eligible=not unmet
    notes=[]
    if requirements.mandatory_attributes and not unmet: notes.append('All mandatory attributes are evidenced in Channel3 structured attributes.')
    if unmet: notes.append('Mandatory attributes are missing or do not match: '+', '.join(unmet)+'.')
    if best_price is not None: notes.append('Best matching-currency offer: '+str(best_price)+' '+requirements.currency+'.')
    if available is True: notes.append('At least one matching-currency offer is marked in stock.')
    elif available is False: notes.append('Matching-currency offers are marked out of stock.')
    if not matching_offers: notes.append('No offers in the requested currency were returned; price and availability are unknown.')
    notes.append('Delivery suitability is unknown because the catalogue response does not establish delivery to the destination.')
    return ProductScore(product_id=product.id,title=product.title,eligible=eligible,score=score.quantize(Decimal('0.01')) if score is not None else None,matched_attributes=matched,unmet_requirements=unmet,best_unit_price=best_price,currency=requirements.currency if best_price is not None else None,available=available,explanation=notes)

def rank_products(products: list[Channel3Product], requirements: ProcurementRequirements) -> list[ProductScore]:
    scored=[score_product(product,requirements) for product in products]
    return sorted(scored,key=lambda item:(item.eligible,item.score is not None,item.score or Decimal(0)),reverse=True)
