import { Modal } from '../common/UI'
import type { Plan } from '../../services/premium'
import { money } from '../../utils/catalogue'

export default function PaymentPreview({ plan, close }: { plan?: Plan; close: () => void }) {
  return <Modal title="Payments coming soon" close={close}>
    {plan && <p>{plan.name} is planned at {money(Number(plan.price))} per month.</p>}
    <p>You can use premium features during the preview without purchasing a subscription.</p>
    <button className="btn primary" onClick={close}>Close payment preview</button>
  </Modal>
}
