"""Seed a visibly OFFLINE sample research request. Never simulate real payments.

Run after signup and migrations:
  cd backend
  .venv/Scripts/python scripts/seed_judge_preview.py --email judge@example.com
  .venv/bin/python scripts/seed_judge_preview.py --email judge@example.com

A sample request cannot create a payable order. Refresh through Channel3 first.
"""
import argparse
import sys
from decimal import Decimal
from pathlib import Path
from sqlalchemy import select

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.integrations.channel3.schemas import Channel3Product,Channel3Offer,Channel3Price
from app.models import ProcurementRequest,User
from app.procurement.policy import requirements_for_request,source_timestamp,evaluate_offer
from app.procurement.scoring import rank_products

SCENARIO='[OFFLINE SAMPLE] Two 27-inch business monitors for a nonprofit office'


def seed_preview(db,user):
    """Return a local preview ID; no third-party calls, tokens or payments."""
    existing=db.scalar(select(ProcurementRequest).where(
        ProcurementRequest.user_id==user.id,
        ProcurementRequest.request_text==SCENARIO,
    ))
    if existing:
        return existing.id
    policy={
        'mandatory_attributes':{'screen_size':'27 inch'},
        'preferred_attributes':{},
        'allowed_merchants':[],
        'max_unit_price':'180.00',
    }
    request=ProcurementRequest(
        user_id=user.id,request_text=SCENARIO,quantity=2,
        budget=Decimal('350.00'),currency='USD',
        policy_json=policy,status='sample_preview',
    )
    db.add(request)
    db.flush()
    products=[
        Channel3Product(id='offline-demo-monitor-27',title='Sample 27-inch monitor (not live stock)',
            structured_attributes={'screen_size':['27 inch']},
            offers=[Channel3Offer(
                url='https://example.invalid/offline-demo-27',
                domain='example.invalid',
                price=Channel3Price(amount=Decimal('140.00'),currency='USD'),
                availability='InStock',
            )]),
        Channel3Product(id='offline-demo-monitor-24',title='Sample 24-inch monitor (wrong specification)',
            structured_attributes={'screen_size':['24 inch']},
            offers=[Channel3Offer(
                url='https://example.invalid/offline-demo-24',
                domain='example.invalid',
                price=Channel3Price(amount=Decimal('90.00'),currency='USD'),
                availability='InStock',
            )]),
        Channel3Product(id='offline-demo-monitor-oos',title='Sample 27-inch monitor (unavailable)',
            structured_attributes={'screen_size':['27 inch']},
            offers=[Channel3Offer(
                url='https://example.invalid/offline-demo-oos',
                domain='example.invalid',
                price=Channel3Price(amount=Decimal('120.00'),currency='USD'),
                availability='OutOfStock',
            )]),
    ]
    scored=rank_products(products,requirements_for_request(request))
    by_id={item.id:item for item in products}
    request.analysis_json={
        'source':'offline_demo',
        'demo_fixture':True,
        'discovered_at':source_timestamp(),
        'results':[{
            'product':by_id[entry.product_id].model_dump(mode='json'),
            'ranking':entry.model_dump(mode='json'),
            'policy':{
                'eligible_offer_urls':[],
                'offer_reasons':{str(offer.url):['OFFLINE SAMPLE: cannot be ordered']
                    +evaluate_offer(request,by_id[entry.product_id],offer)
                    for offer in by_id[entry.product_id].offers},
            },
        } for entry in scored],
        'ai_source':'offline_example',
        'ai_explanation':'Offline explanation only. The 24-inch sample fails the 27-inch requirement; the out-of-stock sample is unavailable. This is not a Gemini response and does not confirm real stock or payment.',
        'ai_usage':None,
        'next_page_available':False,
    }
    db.commit()
    return request.id


def main(argv=None):
    parser=argparse.ArgumentParser(description='Seed a clearly marked non-payable offline judge preview')
    parser.add_argument('--email',required=True,help='Existing registered workspace account')
    args=parser.parse_args(argv)
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email==args.email.strip().casefold()))
        if user is None:
            print('ERROR: Register in the app first; no user created.',file=sys.stderr)
            return 2
        request_id=seed_preview(db,user)
    print('OFFLINE SAMPLE (NOT PAYABLE): /requests/'+request_id)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
