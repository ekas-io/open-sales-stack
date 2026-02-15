import { getStructuredInfo } from "./crawler/get-structured-info";
import { crawlerHelloMethod } from "./crawler/hello";
import { crmHelloMethod } from "./crm/hello";
import { getCompanyDetails } from "./data/coresignal/company/get-company-details";
import { getPeopleDetails } from "./data/coresignal/people/get-people-details";
import { dataHelloMethod } from "./data/hello";
import type { RegisteredMethod } from "./types";

const allMethods = [
  dataHelloMethod,
  crawlerHelloMethod,
  crmHelloMethod,
  getPeopleDetails,
  getCompanyDetails,
  getStructuredInfo
];

export const methodRegistry = new Map<string, RegisteredMethod>(
  allMethods.map((method) => {
    const id = `${method.domain}.${method.name}`;

    return [
      id,
      {
        id,
        domain: method.domain,
        name: method.name,
        description: method.description,
        inputSchema: method.inputSchema,
        execute: method.execute as RegisteredMethod["execute"]
      }
    ];
  })
);

export const methodList = Array.from(methodRegistry.values());
